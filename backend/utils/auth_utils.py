"""
Утилиты для работы с авторизацией
JWT токены, хеширование паролей, валидация
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from core.models import User
from core.schemas import TokenData
import structlog
from cryptography.fernet import Fernet
import base64

logger = structlog.get_logger()

# Настройки для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройки JWT
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-jwt-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180  # 3 часа
REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7 дней


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    # Bcrypt ограничен 72 байтами, обрезаем если нужно
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Создание access токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Создание refresh токена"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_verification_token(email: str) -> str:
    """Создание токена для верификации email"""
    to_encode = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=24),  # 24 часа
        "type": "verification"
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_password_reset_token(email: str) -> str:
    """Создание токена для сброса пароля"""
    to_encode = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=1),  # 1 час
        "type": "password_reset"
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_verification_token(token: str) -> Optional[str]:
    """Проверка токена верификации email и возврат email"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "verification":
            return None
            
        email: str = payload.get("email")
        if email is None:
            return None
            
        return email
        
    except JWTError:
        logger.warning("Verification token validation failed")
        return None


def verify_password_reset_token(token: str) -> Optional[str]:
    """Проверка токена сброса пароля и возврат email"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "password_reset":
            return None
            
        email: str = payload.get("email")
        if email is None:
            return None
            
        return email
        
    except JWTError:
        logger.warning("Password reset token validation failed")
        return None


def verify_token(token: str, token_type: str = "access") -> TokenData:
    """Проверка и декодирование токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Проверяем тип токена
        if payload.get("type") != token_type:
            raise credentials_exception
            
        user_id: int = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")
        
        if user_id is None or email is None:
            raise credentials_exception
            
        token_data = TokenData(user_id=user_id, email=email, role=role)
        return token_data
        
    except JWTError:
        logger.warning("JWT token validation failed", token_type=token_type)
        raise credentials_exception


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Аутентификация пользователя"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        logger.warning("Login attempt with non-existent email", email=email)
        return None
    
    if not verify_password(password, user.hashed_password):
        logger.warning("Login attempt with wrong password", email=email, user_id=user.id)
        return None
    
    if not user.is_active:
        logger.warning("Login attempt with inactive user", email=email, user_id=user.id)
        return None
    
    # Проверяем, подтверждена ли email
    if not user.is_verified:
        logger.warning("Login attempt with unverified email", email=email, user_id=user.id)
        return None
    
    # Обновляем время последнего входа
    user.last_login = datetime.utcnow()
    db.commit()
    
    logger.info("User authenticated successfully", email=email, user_id=user.id, role=user.role)
    return user


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Получение пользователя по ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Получение пользователя по email"""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_data: dict) -> User:
    """Создание нового пользователя"""
    hashed_password = get_password_hash(user_data["password"])
    
    db_user = User(
        email=user_data["email"],
        hashed_password=hashed_password,
        role=user_data.get("role", "user"),
        first_name=user_data.get("first_name"),
        last_name=user_data.get("last_name"),
        is_active=True,
        is_verified=False
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info("New user created", email=db_user.email, user_id=db_user.id, role=db_user.role)
    return db_user


def check_user_permissions(user: User, required_role: str) -> bool:
    """Проверка прав пользователя"""
    role_hierarchy = {
        "user": 1,        # Обычный пользователь
        "admin": 2        # Администратор
    }
    
    user_level = role_hierarchy.get(user.role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level


def get_encryption_key() -> bytes:
    """Получить ключ шифрования из переменной окружения или сгенерировать новый"""
    encryption_key = os.environ.get("ENCRYPTION_KEY")
    
    if not encryption_key:
        # Генерируем новый ключ (только для разработки!)
        encryption_key = Fernet.generate_key().decode()
        logger.warning("No encryption key found in environment, generated new one. Change this in production!")
    
    # Преобразуем строку в bytes если нужно
    if isinstance(encryption_key, str):
        encryption_key = encryption_key.encode()
    
    return encryption_key
