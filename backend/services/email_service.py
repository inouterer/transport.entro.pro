"""
Улучшенный сервис для отправки email с использованием fastapi-mail
Восстановление пароля, подтверждение регистрации
"""

import os
from pathlib import Path
from typing import Optional
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from typing import List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import aiosmtplib
import structlog

logger = structlog.get_logger()


class EmailService:
    """Сервис для отправки email сообщений с использованием fastapi-mail"""
    
    def __init__(self):
        # Путь к шаблонам
        # templates/ находится в /app/templates/ (не в src/)
        template_folder = Path(__file__).parent.parent / "templates" / "email"
        
        # Конфигурация FastMail
        mail_username = os.environ.get("MAIL_USERNAME", "lic@entro.pro")
        mail_password = os.environ.get("MAIL_PASSWORD", "")
        mail_from = os.environ.get("MAIL_FROM", "lic@entro.pro")
        mail_port = int(os.environ.get("MAIL_PORT", "465"))
        mail_server = os.environ.get("MAIL_HOST", "smtp.hoster.ru")
        
        logger.info("Email service configuration", 
                   username=mail_username, 
                   from_addr=mail_from, 
                   server=mail_server, 
                   port=mail_port)
        
        self.conf = ConnectionConfig(
            MAIL_USERNAME=mail_username,
            MAIL_PASSWORD=mail_password,
            MAIL_FROM=mail_from,  # Только email без имени
            MAIL_PORT=mail_port,
            MAIL_SERVER=mail_server,
            MAIL_STARTTLS=False,
            MAIL_SSL_TLS=True,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
            TEMPLATE_FOLDER=str(template_folder)
        )
        
        self.mail_from_name = os.environ.get("MAIL_FROM_NAME", "")  # Пустая строка без имени
        self.frontend_url = os.environ.get("FRONTEND_URL", "http://192.168.72.105:8080")
        self.fm = FastMail(self.conf)
    
    async def send_verification_email(
        self, 
        to: str, 
        verification_token: str, 
        user_name: Optional[str] = None
    ) -> bool:
        """Отправка письма для подтверждения email"""
        try:
            verification_link = f"{self.frontend_url}/verify-email?token={verification_token}"
            greeting = f"Здравствуйте, {user_name}!" if user_name else "Здравствуйте!"
            
            message = MessageSchema(
                subject="Подтверждение регистрации - ЭНТРО.ГТМ",
                recipients=[to],
                sender=("", self.conf.MAIL_FROM),  # Пустое имя, только email
                template_body={
                    "greeting": greeting,
                    "verification_link": verification_link
                },
                subtype=MessageType.html,
            )
            
            await self.fm.send_message(message, template_name="verification.html")
            logger.info("Verification email sent successfully", to=to)
            return True
            
        except Exception as e:
            logger.error("Failed to send verification email", to=to, error=str(e))
            return False
    
    async def send_password_reset_email(
        self, 
        to: str, 
        reset_token: str, 
        user_name: Optional[str] = None
    ) -> bool:
        """Отправка письма для восстановления пароля"""
        try:
            reset_link = f"{self.frontend_url}/reset-password?token={reset_token}"
            greeting = f"Здравствуйте, {user_name}!" if user_name else "Здравствуйте!"
            
            message = MessageSchema(
                subject="Восстановление пароля - ЭНТРО.ГТМ",
                recipients=[to],
                sender=("", self.conf.MAIL_FROM),  # Пустое имя, только email
                template_body={
                    "greeting": greeting,
                    "reset_link": reset_link
                },
                subtype=MessageType.html,
            )
            
            await self.fm.send_message(message, template_name="password_reset.html")
            logger.info("Password reset email sent successfully", to=to)
            return True
            
        except Exception as e:
            logger.error("Failed to send password reset email", to=to, error=str(e))
            return False
    
    async def send_welcome_email(
        self, 
        to: str, 
        user_name: Optional[str] = None
    ) -> bool:
        """Отправка приветственного письма"""
        try:
            greeting = f"Здравствуйте, {user_name}!" if user_name else "Здравствуйте!"
            
            message = MessageSchema(
                subject="Добро пожаловать в ЭНТРО.ГТМ!",
                recipients=[to],
                sender=("", self.conf.MAIL_FROM),  # Пустое имя, только email
                template_body={
                    "greeting": greeting,
                    "frontend_url": self.frontend_url,
                    "support_email": self.conf.MAIL_FROM
                },
                subtype=MessageType.html,
            )
            
            await self.fm.send_message(message, template_name="welcome.html")
            logger.info("Welcome email sent successfully", to=to)
            return True
            
        except Exception as e:
            logger.error("Failed to send welcome email", to=to, error=str(e))
            return False


    async def send_new_user_credentials_email(
        self, 
        to: str, 
        password: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Отправка письма с учетными данными новому пользователю, созданному админом"""
        try:
            logger.info("Sending new user credentials email", to=to)
            login_link = f"{self.frontend_url}/login"
            greeting = f"Здравствуйте, {user_name}!" if user_name else "Здравствуйте!"
            
            message = MessageSchema(
                subject="Ваш аккаунт в системе cloud.entro.pro создан",
                recipients=[to],
                template_body={
                    "greeting": greeting,
                    "login_link": login_link,
                    "email": to,
                    "password": password
                },
                subtype=MessageType.html,
            )
            
            await self.fm.send_message(message, template_name="new_user_credentials.html")
            logger.info("New user credentials email sent successfully", to=to)
            return True
            
        except Exception as e:
            logger.error("Failed to send new user credentials email", to=to, error=str(e))
            return False


# Создаем глобальный экземпляр сервиса
email_service = EmailService()
