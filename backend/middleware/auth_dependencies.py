"""
Зависимости FastAPI для авторизации
Получение текущего пользователя, проверка прав доступа
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from core.database import get_db
from core.models import User
from utils.auth_utils import verify_token, get_user_by_id, check_user_permissions
import structlog

logger = structlog.get_logger()

# Схема для Bearer токена
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Получение текущего пользователя по токену"""
    logger.info(f"get_current_user called, credentials present: {credentials is not None}")
    token = credentials.credentials
    token_data = verify_token(token, "access")
    logger.info(f"Token verified, user_id: {token_data.user_id}")
    
    user = get_user_by_id(db, user_id=token_data.user_id)
    if user is None:
        logger.warning("User not found for token", user_id=token_data.user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        logger.warning("Inactive user attempted access", user_id=user.id, email=user.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь деактивирован",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Получение активного пользователя"""
    return current_user


def require_role(required_role: str):
    """Декоратор для проверки роли пользователя"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not check_user_permissions(current_user, required_role):
            logger.warning(
                "Insufficient permissions",
                user_id=current_user.id,
                user_role=current_user.role,
                required_role=required_role
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется роль: {required_role}"
            )
        return current_user
    return role_checker


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Требование роли администратора"""
    return require_role("admin")(current_user)




def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Получение текущего пользователя (опционально)"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        token_data = verify_token(token, "access")
        user = get_user_by_id(db, user_id=token_data.user_id)
        return user if user and user.is_active else None
    except HTTPException:
        return None
