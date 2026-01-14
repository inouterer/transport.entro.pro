from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, LargeBinary, Float
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base
import uuid


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="user", nullable=False)  # admin, user
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Связи
    project_permissions = relationship("ProjectPermission", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # Псевдоним проекта
    db_host = Column(String(255), nullable=False)  # Хост БД
    db_port = Column(Integer, default=5432, nullable=False)  # Порт БД
    db_name = Column(String(255), nullable=False)  # Название БД
    db_user = Column(String(255), nullable=False)  # Пользователь БД
    db_password = Column(String(255), nullable=False)  # Пароль БД (зашифрованный)
    connection_type = Column(String(50), default="direct", nullable=False)  # direct, vpn
    is_active = Column(Boolean, default=True, nullable=False)  # Статус подключения
    connection_status = Column(String(50), default="unknown", nullable=False)  # online, offline, error
    last_check = Column(DateTime(timezone=True), nullable=True)  # Последняя проверка подключения
    description = Column(Text, nullable=True)  # Описание проекта
    image_data = Column(LargeBinary, nullable=True)  # Изображение проекта (BLOB)
    image_mime_type = Column(String(50), nullable=True)  # MIME тип изображения (image/jpeg, image/png и т.д.)
    project_metadata = Column('metadata', JSONB, nullable=True)  # Дополнительные метаданные проекта (JSON)
    display_order = Column(Integer, default=0, nullable=False)  # Порядок отображения проектов
    north_azimuth_correction = Column(Float, default=0.0, nullable=False)  # Угол корректировки азимута севера (градусы)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    permissions = relationship("ProjectPermission", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', host='{self.db_host}')>"


class ProjectPermission(Base):
    __tablename__ = "project_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)  # operator, manager, viewer, no_access
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    user = relationship("User", back_populates="project_permissions")
    project = relationship("Project", back_populates="permissions")
    
    # Уникальный индекс для комбинации пользователя и проекта
    __table_args__ = ({"extend_existing": True})
    
    def __repr__(self):
        return f"<ProjectPermission(user_id={self.user_id}, project_id={self.project_id}, role='{self.role}')>"


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(String(50), nullable=False, index=True)  # admin, user, project
    action_type = Column(String(100), nullable=False, index=True)  # admin.user.create, user.auth.login, project.data.view
    action_name = Column(String(255), nullable=False)  # "Создание пользователя", "Вход в систему"
    resource_type = Column(String(50), nullable=True)  # user, project, permission, cycle, scheduler_task
    resource_id = Column(String(255), nullable=True)  # ID ресурса (может быть не только int)
    details = Column(JSONB, nullable=True)  # Дополнительные данные в JSON формате
    ip_address = Column(String(45), nullable=True)  # IPv4 или IPv6
    user_agent = Column(Text, nullable=True)  # User-Agent браузера
    request_method = Column(String(10), nullable=True)  # GET, POST, PUT, DELETE
    request_path = Column(String(500), nullable=True)  # Путь запроса
    status = Column(String(20), default="success", nullable=False)  # success, error
    error_message = Column(Text, nullable=True)  # Сообщение об ошибке, если status=error
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Связи
    user = relationship("User", foreign_keys=[user_id])
    project = relationship("Project", foreign_keys=[project_id])
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action='{self.action_name}', category='{self.category}')>"


class GeologyEgeCatalogGlobal(Base):
    """
    Общий справочник ИГЭ (Инженерно-геологических элементов)
    Хранится в центральной БД, доступен для всех проектов
    Data-Driven UI: метаданные хранятся в комментариях PostgreSQL
    """
    __tablename__ = "geology_ege_catalog_global"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)  # Код ИГЭ (уникален глобально)
    name = Column(String(255), nullable=False)  # Наименование
    description = Column(Text, nullable=True)  # Примечание
    
    # Визуализация
    hatch_pattern_name = Column(String(100), nullable=True)  # Имя файла штриховки
    hatch_scale = Column(Float, default=0.5, nullable=False)  # Масштаб штриховки
    color_hex = Column(String(7), default='#FFFFFF', nullable=False)  # Цвет фона (Hex)
    
    # Физические свойства (базовые)
    rho = Column(Float, nullable=True)  # Плотность
    rho_s = Column(Float, nullable=True)  # Плотность частиц
    rho_d = Column(Float, nullable=True)  # Плотность скелета
    e_void = Column(Float, nullable=True)  # Коэф. пористости
    n_porosity = Column(Float, nullable=True)  # Пористость
    w_tot = Column(Float, nullable=True)  # Влажность
    sr = Column(Float, nullable=True)  # Степень водонасыщения
    
    # Пластичность
    w_l = Column(Float, nullable=True)  # Влажность на границе текучести
    w_p = Column(Float, nullable=True)  # Влажность на границе пластичности
    ip = Column(Float, nullable=True)  # Число пластичности
    il = Column(Float, nullable=True)  # Показатель текучести
    
    # Механика (общая)
    e_mod = Column(Float, nullable=True)  # Модуль деформации
    c_coh = Column(Float, nullable=True)  # Сцепление
    phi = Column(Float, nullable=True)  # Угол трения
    
    # Теплофизика
    t_bf = Column(Float, nullable=True)  # Tbf: Температура начала замерзания
    lambda_th = Column(Float, nullable=True)  # LMBth: Теплопроводность (талый)
    lambda_f = Column(Float, nullable=True)  # LMBf: Теплопроводность (мерзлый)
    c_th_vol = Column(Float, nullable=True)  # Cth: Теплоемкость объемная (талый)
    c_f_vol = Column(Float, nullable=True)  # Cf: Теплоемкость объемная (мерзлый)
    q_ph = Column(Float, nullable=True)  # Qf: Удельная теплота фазового перехода
    
    # Мерзлые грунты (СП 25)
    i_tot = Column(Float, nullable=True)  # Льдистость суммарная
    i_i = Column(Float, nullable=True)  # Степень заполнения льдом
    d_sal = Column(Float, default=0.0, nullable=False)  # Засоленность Dsal, %
    salinization_type = Column(String(50), default='NON_SALINE', nullable=False)  # Тип засоления
    soil_type_sp25 = Column(String(50), nullable=True)  # Тип грунта (СП 25)
    sand_granularity = Column(String(50), nullable=True)  # Крупность песка
    
    # Опытные данные
    raf_exp = Column(Float, nullable=True)  # Raf опытная (срез)
    r_c_exp = Column(Float, nullable=True)  # R опытная (сжатие)
    
    is_active = Column(Boolean, default=True, nullable=False)  # Активен ли ИГЭ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<GeologyEgeCatalogGlobal(id={self.id}, code='{self.code}', name='{self.name}')>"
