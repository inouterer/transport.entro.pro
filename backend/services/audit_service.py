from sqlalchemy.orm import Session
from fastapi import Request
from typing import Optional, Dict, Any
from core.models import AuditLog
import structlog

logger = structlog.get_logger()

class AuditService:
    @staticmethod
    async def log_action(
        db: Session,
        user_id: Optional[int],
        category: str,
        action_type: str,
        action_name: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        project_id: Optional[int] = None
    ):
        """
        Логирование действий пользователя в базу данных и в лог-файл (через structlog)
        """
        try:
            # Сбор данных из запроса
            ip_address = None
            user_agent = None
            request_method = None
            request_path = None

            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
                request_method = request.method
                request_path = str(request.url.path)

            # Создание записи в БД
            audit_log = AuditLog(
                user_id=user_id,
                project_id=project_id,
                category=category,
                action_type=action_type,
                action_name=action_name,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                request_method=request_method,
                request_path=request_path,
                status=status,
                error_message=error_message
            )
            
            db.add(audit_log)
            db.commit()

            # Логирование через structlog
            log_data = {
                "event": action_type,
                "user_id": user_id,
                "category": category,
                "status": status,
                "action_name": action_name
            }
            if details:
                log_data["details"] = details
            if error_message:
                log_data["error"] = error_message

            if status == "success":
                logger.info("Audit log entry created", **log_data)
            else:
                logger.warning("Audit log entry created (with error)", **log_data)

        except Exception as e:
            # Не бросаем исключение выше, чтобы ошибка логирования не прерывала основной процесс
            logger.error("Failed to create audit log entry", error=str(e), action_type=action_type)
            db.rollback()
