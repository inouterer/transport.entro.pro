"""
Эндпоинты авторизации
Регистрация, вход, обновление токенов, выход
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import timedelta
from core.database import get_db
from core.models import User
from core.schemas import (
    UserCreate, UserResponse, LoginRequest, TokenResponse, 
    RefreshTokenRequest, AuthResponse, MessageResponse,
    EmailRequest, PasswordResetRequest
)
from utils.auth_utils import (
    authenticate_user, create_user, create_access_token, 
    create_refresh_token, verify_token, get_user_by_email,
    create_verification_token, create_password_reset_token,
    verify_verification_token, verify_password_reset_token,
    get_password_hash
)
from middleware.auth_dependencies import get_current_active_user
from services.email_service import email_service
from services.audit_service import AuditService
import structlog

logger = structlog.get_logger()

# Создаем роутер для авторизации
# Префикс /v1/auth т.к. nginx проксирует /api/ -> http://api:8000/
auth_router = APIRouter(prefix="/v1/auth", tags=["Авторизация"])


@auth_router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Регистрация нового пользователя"""
    
    # Проверяем, не существует ли уже пользователь с таким email
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        logger.warning("Registration attempt with existing email", email=user_data.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )
    
    # Создаем нового пользователя
    # Роль всегда устанавливается в "viewer" при регистрации
    # Администратор может изменить роль позже
    try:
        user_dict = user_data.dict()
        user_dict["role"] = "user"  # Принудительно устанавливаем роль user
        user = create_user(db, user_dict)
        
        # Отправляем письмо подтверждения
        logger.info("Attempting to send verification email", email=user.email, user_id=user.id)
        verification_token = create_verification_token(user.email)
        user_name = f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else user.first_name
        
        try:
            email_sent = await email_service.send_verification_email(
                to=user.email,
                verification_token=verification_token,
                user_name=user_name
            )
            
            if email_sent:
                logger.info("Verification email sent successfully", email=user.email)
            else:
                logger.warning("Failed to send verification email", email=user.email)
        except Exception as e:
            logger.error("Exception sending verification email", email=user.email, error=str(e))
        
        # НЕ создаем токены - пользователь должен подтвердить email сначала
        # Принудительно устанавливаем is_verified в False если оно было True
        if user.is_verified:
            user.is_verified = False
            db.commit()
        
        # Создаем пустые токены (фронтенд должен перенаправить на страницу подтверждения)
        empty_tokens = TokenResponse(
            access_token="",
            refresh_token="",
            token_type="bearer",
            expires_in=0
        )
        
        logger.info("User registered successfully, awaiting email verification", email=user.email, user_id=user.id)
        
        # Логируем регистрацию
        try:
            await AuditService.log_action(
                db=db,
                user_id=user.id,
                category="user",
                action_type="user.auth.register",
                action_name=f"Регистрация пользователя {user.email}",
                resource_type="user",
                resource_id=str(user.id),
                details={
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                },
                request=request
            )
        except Exception as audit_err:
            logger.warning("Failed to log audit action", error=str(audit_err))
        
        return AuthResponse(
            user=UserResponse.from_orm(user),
            tokens=empty_tokens
        )
        
    except Exception as e:
        logger.error("Registration failed", email=user_data.email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании пользователя"
        )


@auth_router.post("/login", response_model=AuthResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Вход в систему"""
    
    # Аутентификация пользователя
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        # Проверяем, существует ли пользователь
        existing_user = get_user_by_email(db, login_data.email)
        if existing_user and not existing_user.is_verified:
            logger.warning("Login attempt with unverified email", email=login_data.email)
            # Логируем неуспешную попытку входа
            try:
                await AuditService.log_action(
                    db=db,
                    user_id=existing_user.id if existing_user else None,
                    category="user",
                    action_type="user.auth.login",
                    action_name=f"Попытка входа (email не подтвержден) - {login_data.email}",
                    resource_type="user",
                    resource_id=str(existing_user.id) if existing_user else None,
                    details={"email": login_data.email},
                    request=request,
                    status="error",
                    error_message="Email не подтвержден"
                )
            except Exception as audit_err:
                logger.warning("Failed to log audit action", error=str(audit_err))
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email не подтвержден. Пожалуйста, проверьте почту и подтвердите регистрацию.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.warning("Login failed", email=login_data.email)
        # Логируем неуспешную попытку входа (неправильный пароль)
        try:
            await AuditService.log_action(
                db=db,
                user_id=existing_user.id if existing_user else None,
                category="user",
                action_type="user.auth.login",
                action_name=f"Неуспешная попытка входа - {login_data.email}",
                resource_type="user",
                resource_id=str(existing_user.id) if existing_user else None,
                details={"email": login_data.email},
                request=request,
                status="error",
                error_message="Неверный email или пароль"
            )
        except Exception as audit_err:
            logger.warning("Failed to log audit action", error=str(audit_err))
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаем токены
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )
    
    tokens = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )
    
    logger.info("User logged in successfully", email=user.email, user_id=user.id)
    
    # Логируем успешный вход
    try:
        await AuditService.log_action(
            db=db,
            user_id=user.id,
            category="user",
            action_type="user.auth.login",
            action_name=f"Вход в систему - {user.email}",
            resource_type="user",
            resource_id=str(user.id),
            details={"email": user.email, "role": user.role},
            request=request
        )
    except Exception as audit_err:
        logger.warning("Failed to log audit action", error=str(audit_err))
    
    return AuthResponse(
        user=UserResponse.from_orm(user),
        tokens=tokens
    )


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Обновление access токена"""
    
    try:
        # Проверяем refresh токен
        token_data = verify_token(refresh_data.refresh_token, "refresh")
        
        # Получаем пользователя
        user = db.query(User).filter(User.id == token_data.user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь не найден или деактивирован"
            )
        
        # Создаем новые токены
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )
        new_refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )
        
        logger.info("Tokens refreshed", user_id=user.id, email=user.email)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный refresh токен"
        )


@auth_router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Выход из системы"""
    
    # В текущей реализации просто логируем выход
    # В будущем можно добавить blacklist токенов в Redis
    logger.info("User logged out", user_id=current_user.id, email=current_user.email)
    
    # Логируем выход
    try:
        await AuditService.log_action(
            db=db,
            user_id=current_user.id,
            category="user",
            action_type="user.auth.logout",
            action_name=f"Выход из системы - {current_user.email}",
            resource_type="user",
            resource_id=str(current_user.id),
            details={"email": current_user.email},
            request=request
        )
    except Exception as audit_err:
        logger.warning("Failed to log audit action", error=str(audit_err))
    
    return MessageResponse(
        message="Успешный выход из системы",
        success=True
    )


@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Получение информации о текущем пользователе"""
    return UserResponse.from_orm(current_user)


@auth_router.post("/verify-token", response_model=MessageResponse)
async def verify_token_endpoint(
    current_user: User = Depends(get_current_active_user)
):
    """Проверка валидности токена"""
    return MessageResponse(
        message="Токен действителен",
        success=True
    )


@auth_router.get("/verify-email", response_model=MessageResponse)
async def verify_email(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Подтверждение email по токену"""
    
    # Проверяем токен
    email = verify_verification_token(token)
    if not email:
        logger.warning("Invalid verification token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный или истекший токен подтверждения"
        )
    
    # Находим пользователя
    user = get_user_by_email(db, email)
    if not user:
        logger.warning("User not found for verification", email=email)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Проверяем, не подтвержден ли уже
    if user.is_verified:
        logger.info("Email already verified", email=email)
        return MessageResponse(
            message="Email уже подтвержден",
            success=True
        )
    
    # Подтверждаем email
    user.is_verified = True
    db.commit()
    
    # Отправляем приветственное письмо
    user_name = f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else user.first_name
    await email_service.send_welcome_email(user.email, user_name)
    
    logger.info("Email verified successfully", email=email, user_id=user.id)
    
    # Логируем подтверждение email
    try:
        await AuditService.log_action(
            db=db,
            user_id=user.id,
            category="user",
            action_type="user.auth.verify_email",
            action_name=f"Подтверждение email - {user.email}",
            resource_type="user",
            resource_id=str(user.id),
            details={"email": user.email},
            request=request
        )
    except Exception as audit_err:
        logger.warning("Failed to log audit action", error=str(audit_err))
    
    return MessageResponse(
        message="Email успешно подтвержден!",
        success=True
    )


@auth_router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    email_request: EmailRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Запрос на восстановление пароля"""
    
    # Находим пользователя
    user = get_user_by_email(db, email_request.email)
    if not user:
        # Не раскрываем, существует ли пользователь
        # Не логируем для безопасности (чтобы не раскрывать существование пользователя)
        logger.warning("Password reset requested for non-existent email", email=email_request.email)
        return MessageResponse(
            message="Если пользователь с таким email существует, письмо с инструкциями будет отправлено",
            success=True
        )
    
    # Создаем токен сброса пароля
    reset_token = create_password_reset_token(user.email)
    
    # Отправляем письмо
    user_name = f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else user.first_name
    email_sent = await email_service.send_password_reset_email(
        to=user.email,
        reset_token=reset_token,
        user_name=user_name
    )
    
    if email_sent:
        logger.info("Password reset email sent", email=email_request.email)
        # Логируем запрос на сброс пароля
        try:
            await AuditService.log_action(
                db=db,
                user_id=user.id,
                category="user",
                action_type="user.auth.forgot_password",
                action_name=f"Запрос на восстановление пароля - {user.email}",
                resource_type="user",
                resource_id=str(user.id),
                details={"email": user.email},
                request=request
            )
        except Exception as audit_err:
            logger.warning("Failed to log audit action", error=str(audit_err))
    else:
        logger.error("Failed to send password reset email", email=email_request.email)
    
    return MessageResponse(
        message="Если пользователь с таким email существует, письмо с инструкциями будет отправлено",
        success=True
    )


@auth_router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    reset_request: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Сброс пароля по токену"""
    
    # Проверяем токен
    email = verify_password_reset_token(reset_request.token)
    if not email:
        logger.warning("Invalid password reset token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный или истекший токен сброса пароля"
        )
    
    # Находим пользователя
    user = get_user_by_email(db, email)
    if not user:
        logger.warning("User not found for password reset", email=email)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Обновляем пароль
    user.hashed_password = get_password_hash(reset_request.new_password)
    db.commit()
    
    logger.info("Password reset successfully", email=email, user_id=user.id)
    
    # Логируем сброс пароля
    try:
        await AuditService.log_action(
            db=db,
            user_id=user.id,
            category="user",
            action_type="user.auth.reset_password",
            action_name=f"Сброс пароля - {user.email}",
            resource_type="user",
            resource_id=str(user.id),
            details={"email": user.email},
            request=request
        )
    except Exception as audit_err:
        logger.warning("Failed to log audit action", error=str(audit_err))
    
    return MessageResponse(
        message="Пароль успешно изменен!",
        success=True
    )


@auth_router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    request: EmailRequest,
    db: Session = Depends(get_db)
):
    """Повторная отправка письма подтверждения"""
    
    # Находим пользователя
    user = get_user_by_email(db, request.email)
    if not user:
        # Не раскрываем, существует ли пользователь
        logger.warning("Verification resend requested for non-existent email", email=request.email)
        return MessageResponse(
            message="Если пользователь с таким email существует и не подтвержден, письмо будет отправлено",
            success=True
        )
    
    # Проверяем, не подтвержден ли уже
    if user.is_verified:
        logger.info("Verification resend requested for already verified user", email=request.email)
        return MessageResponse(
            message="Email уже подтвержден",
            success=True
        )
    
    # Создаем новый токен
    verification_token = create_verification_token(user.email)
    
    # Отправляем письмо
    user_name = f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else user.first_name
    email_sent = await email_service.send_verification_email(
        to=user.email,
        verification_token=verification_token,
        user_name=user_name
    )
    
    if email_sent:
        logger.info("Verification email resent", email=request.email)
    else:
        logger.error("Failed to resend verification email", email=request.email)
    
    return MessageResponse(
        message="Письмо с подтверждением отправлено повторно",
        success=True
    )
