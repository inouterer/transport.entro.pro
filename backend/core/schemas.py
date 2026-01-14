from pydantic import BaseModel, EmailStr, Field, validator, field_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from fastapi import UploadFile
import base64


# Схемы для пользователей
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "user"  # admin, user


class UserCreateAdmin(UserBase):
    pass


class ProjectBase(BaseModel):
    name: str  # Псевдоним проекта
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    db_host: str  # Хост БД
    db_port: int = 5432  # Порт БД
    db_name: str  # Название БД
    db_user: str  # Пользователь БД
    db_password: str  # Пароль БД
    connection_type: str = "direct"  # direct, vpn


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    db_host: Optional[str] = None
    db_port: Optional[int] = None
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    connection_type: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    north_azimuth_correction: Optional[float] = Field(None, description="Угол корректировки азимута севера (градусы), 0 по умолчанию")


class ProjectResponse(BaseModel):
    id: int
    name: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    connection_type: str
    is_active: bool
    connection_status: str
    last_check: Optional[datetime] = None
    description: Optional[str] = None
    display_order: int = 0
    north_azimuth_correction: float = 0.0
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProjectPermissionGrant(BaseModel):
    user_email: str
    project_id: int
    role: str  # operator, manager, viewer, no_access


class ProjectPermissionUpdate(BaseModel):
    role: str  # operator, manager, viewer, no_access


class ProjectPermissionResponse(BaseModel):
    id: int
    user_id: int
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    project_id: int
    project_name: Optional[str] = None
    role: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        if not any(c.isupper() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну заглавную букву')
        if not any(c.islower() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну строчную букву')
        if not any(c.isdigit() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # Pydantic v2


# Схемы для авторизации
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 минут


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None


# Схемы для ответов API
class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class EmailRequest(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


# Схемы для планировщика работ
class SchedulerTaskCreate(BaseModel):
    subobject_id: int
    cycle_id: int
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD


class SchedulerTaskUpdate(BaseModel):
    cycle_id: Optional[int] = None
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None  # YYYY-MM-DD


class SchedulerTaskResponse(BaseModel):
    id: int
    subobject_id: int
    subobject_name: str
    object_id: int
    object_name: str
    cycle_id: int
    cycle_number: Optional[int] = None
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    total_positions: int
    completed_positions: int
    progress: float  # 0-100
    status: str  # planned, in_progress, completed
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    # Детальная статистика по типам элементов
    total_dm_elements: Optional[int] = None
    completed_dm_elements: Optional[int] = None
    total_ts_elements: Optional[int] = None
    completed_ts_elements: Optional[int] = None


# Схемы для циклов
class CycleCreate(BaseModel):
    number: int
    date_start: Optional[str] = None  # YYYY-MM-DD
    date_end: Optional[str] = None  # YYYY-MM-DD
    description: Optional[str] = None


class CycleUpdate(BaseModel):
    number: Optional[int] = None
    date_start: Optional[str] = None  # YYYY-MM-DD
    date_end: Optional[str] = None  # YYYY-MM-DD
    description: Optional[str] = None


class CycleResponse(BaseModel):
    cycle_id: int
    number: int
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    description: Optional[str] = None
    has_data: bool = False
    cycle_status: int = 0  # 0=план, 1=активный, 2=завершенный


# Схемы для логирования действий
class AuditLogResponse(BaseModel):
    id: UUID
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    category: str
    action_type: str
    action_name: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_method: Optional[str] = None
    request_path: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int


class AuditLogFilter(BaseModel):
    user_id: Optional[int] = None
    project_id: Optional[int] = None
    category: Optional[str] = None
    action_type: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


# Схемы для metadata проектов
class ProjectMetadataResponse(BaseModel):
    completed_cycles: List[int] = []
    current_cycle_id: Optional[int] = None
    planned_cycle_id: Optional[int] = None
    excluded_positions: List[int] = []


class ProjectMetadataUpdate(BaseModel):
    completed_cycles: Optional[List[int]] = None
    current_cycle_id: Optional[int] = Field(None, description="ID текущего цикла, -1 для удаления")
    planned_cycle_id: Optional[int] = Field(None, description="ID планируемого цикла, -1 для удаления")
    excluded_positions: Optional[List[int]] = None


# Схемы для параметров позиций (positions_attributes)
class PositionAttributeBase(BaseModel):
    temperature_deep_min: Optional[float] = None
    relativediff: Optional[float] = None
    averagediff: Optional[float] = None
    roll: Optional[float] = None
    constr_height: Optional[float] = None
    norm_id: Optional[int] = None
    temperature_deep_max: Optional[float] = None
    temperature_bf: Optional[float] = None  # Температура начала замерзания (Tbf)
    temperature_h: Optional[float] = None  # Температура границы твердомерздого состояния (Th)
    base_depth: Optional[float] = None  # Глубина заложения фундамента (свай)


class PositionAttributeUpdate(PositionAttributeBase):
    position_id: int


class PositionAttributeResponse(PositionAttributeBase):
    object_id: int
    object_name: str
    subobject_id: int
    subobject_name: str
    position_id: int
    position_name: str
    position_type: int
    attr_id: Optional[int] = None

    class Config:
        from_attributes = True


class PositionAttributesBulkUpdate(BaseModel):
    attributes: List[PositionAttributeUpdate]


class PositionAttributesCopyRequest(BaseModel):
    source_position_id: int
    target_type: str = Field(..., description="Тип цели: 'position', 'subobject', 'object' или 'project'")
    target_id: Optional[int] = Field(None, description="ID цели (position_id, subobject_id или object_id). Не требуется для 'project'")


class PositionAttributesDeleteRequest(BaseModel):
    position_ids: List[int]


# ==================== Схемы для геологии ====================

class GeologyEgeCatalogResponse(BaseModel):
    """
    Справочник ИГЭ (проектный) - Data-Driven UI
    Принимает любые дополнительные поля из таблицы
    """
    # Обязательные поля
    ege_id: int
    project_id: Optional[int]
    code: str
    name: str
    description: Optional[str] = None
    
    # Визуализация (обязательные для UI)
    hatch_pattern_name: Optional[str] = None
    hatch_scale: Optional[float] = 0.5
    color_hex: Optional[str] = "#FFFFFF"
    
    class Config:
        from_attributes = True
        extra = 'allow'  # Разрешаем любые дополнительные поля


class GeologyEgeCatalogGlobalResponse(BaseModel):
    """Общий справочник ИГЭ (центральная БД) - Data-Driven UI"""
    id: int
    code: str
    name: str
    description: Optional[str] = None
    
    # Визуализация
    hatch_pattern_name: Optional[str] = None
    hatch_scale: Optional[float] = 0.5
    color_hex: Optional[str] = "#FFFFFF"
    
    # Физические свойства (базовые)
    rho: Optional[float] = None
    rho_s: Optional[float] = None
    rho_d: Optional[float] = None
    e_void: Optional[float] = None
    n_porosity: Optional[float] = None
    w_tot: Optional[float] = None
    sr: Optional[float] = None
    
    # Пластичность
    w_l: Optional[float] = None
    w_p: Optional[float] = None
    ip: Optional[float] = None
    il: Optional[float] = None
    
    # Механика (общая)
    e_mod: Optional[float] = None
    c_coh: Optional[float] = None
    phi: Optional[float] = None
    
    # Теплофизика
    t_bf: Optional[float] = None
    lambda_th: Optional[float] = None
    lambda_f: Optional[float] = None
    c_th_vol: Optional[float] = None
    c_f_vol: Optional[float] = None
    q_ph: Optional[float] = None
    
    # Мерзлые грунты (СП 25)
    i_tot: Optional[float] = None
    i_i: Optional[float] = None
    d_sal: Optional[float] = 0.0
    salinization_type: Optional[str] = "NON_SALINE"
    soil_type_sp25: Optional[str] = None
    sand_granularity: Optional[str] = None
    
    # Опытные данные
    raf_exp: Optional[float] = None
    r_c_exp: Optional[float] = None
    
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class GeologyEgeCatalogCreate(BaseModel):
    """
    Создание ИГЭ в проекте - Data-Driven UI
    Принимает любые дополнительные поля из таблицы
    """
    # Обязательные поля
    code: str
    name: str
    description: Optional[str] = None
    
    # Визуализация (стандартные значения)
    hatch_pattern_name: Optional[str] = None
    hatch_scale: Optional[float] = Field(default=0.5, ge=0.05, le=5.0)
    color_hex: Optional[str] = "#FFFFFF"
    
    class Config:
        extra = 'allow'  # Разрешаем любые дополнительные поля


class GeologyEgeCatalogUpdate(BaseModel):
    """
    Обновление ИГЭ в проекте - Data-Driven UI
    Принимает любые дополнительные поля из таблицы
    """
    # Все поля опциональные для обновления
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    
    # Визуализация
    hatch_pattern_name: Optional[str] = None
    hatch_scale: Optional[float] = Field(default=None, ge=0.05, le=5.0)
    color_hex: Optional[str] = None
    
    class Config:
        extra = 'allow'  # Разрешаем любые дополнительные поля


class GeologyEgeCatalogGlobalCreate(BaseModel):
    """Создание ИГЭ в общем справочнике - Data-Driven UI"""
    code: str
    name: str
    description: Optional[str] = None
    
    # Визуализация
    hatch_pattern_name: Optional[str] = None
    hatch_scale: Optional[float] = Field(default=0.5, ge=0.05, le=5.0)
    color_hex: Optional[str] = "#FFFFFF"
    
    # Физические свойства (базовые)
    rho: Optional[float] = None
    rho_s: Optional[float] = None
    rho_d: Optional[float] = None
    e_void: Optional[float] = None
    n_porosity: Optional[float] = None
    w_tot: Optional[float] = None
    sr: Optional[float] = None
    
    # Пластичность
    w_l: Optional[float] = None
    w_p: Optional[float] = None
    ip: Optional[float] = None
    il: Optional[float] = None
    
    # Механика (общая)
    e_mod: Optional[float] = None
    c_coh: Optional[float] = None
    phi: Optional[float] = None
    
    # Теплофизика
    t_bf: Optional[float] = None
    lambda_th: Optional[float] = None
    lambda_f: Optional[float] = None
    c_th_vol: Optional[float] = None
    c_f_vol: Optional[float] = None
    q_ph: Optional[float] = None
    
    # Мерзлые грунты (СП 25)
    i_tot: Optional[float] = None
    i_i: Optional[float] = None
    d_sal: Optional[float] = 0.0
    salinization_type: Optional[str] = "NON_SALINE"
    soil_type_sp25: Optional[str] = None
    sand_granularity: Optional[str] = None
    
    # Опытные данные
    raf_exp: Optional[float] = None
    r_c_exp: Optional[float] = None
    
    is_active: bool = True


class GeologyEgeCatalogGlobalUpdate(BaseModel):
    """Обновление ИГЭ в общем справочнике - Data-Driven UI"""
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    
    # Визуализация
    hatch_pattern_name: Optional[str] = None
    hatch_scale: Optional[float] = Field(default=None, ge=0.05, le=5.0)
    color_hex: Optional[str] = None
    
    # Физические свойства (базовые)
    rho: Optional[float] = None
    rho_s: Optional[float] = None
    rho_d: Optional[float] = None
    e_void: Optional[float] = None
    n_porosity: Optional[float] = None
    w_tot: Optional[float] = None
    sr: Optional[float] = None
    
    # Пластичность
    w_l: Optional[float] = None
    w_p: Optional[float] = None
    ip: Optional[float] = None
    il: Optional[float] = None
    
    # Механика (общая)
    e_mod: Optional[float] = None
    c_coh: Optional[float] = None
    phi: Optional[float] = None
    
    # Теплофизика
    t_bf: Optional[float] = None
    lambda_th: Optional[float] = None
    lambda_f: Optional[float] = None
    c_th_vol: Optional[float] = None
    c_f_vol: Optional[float] = None
    q_ph: Optional[float] = None
    
    # Мерзлые грунты (СП 25)
    i_tot: Optional[float] = None
    i_i: Optional[float] = None
    d_sal: Optional[float] = None
    salinization_type: Optional[str] = None
    soil_type_sp25: Optional[str] = None
    sand_granularity: Optional[str] = None
    
    # Опытные данные
    raf_exp: Optional[float] = None
    r_c_exp: Optional[float] = None
    
    is_active: Optional[bool] = None


class CopyEgeFromGlobalRequest(BaseModel):
    """Запрос на копирование ИГЭ из общего справочника"""
    global_ege_id: int  # ID из общего справочника


class CopyEgeFromProjectRequest(BaseModel):
    """Запрос на копирование ИГЭ из проектного справочника в общий справочник"""
    project_ege_id: int  # ID ИГЭ из проектного справочника


class GeologyElementResponse(BaseModel):
    """Геологическая скважина"""
    element_id: int
    position_id: Optional[int]
    name: str
    x: Optional[float]
    y: Optional[float]
    z: Optional[float]
    drilling_date: Optional[str] = None
    ground_water_level: Optional[float] = None
    description: Optional[str] = None
    created_at: Optional[str] = None


class GeologyLayerResponse(BaseModel):
    """Слой литологии с вычисленными свойствами"""
    layer_id: int
    element_id: int
    depth_from: float
    depth_to: float
    thickness: float  # Вычисляемое в Python коде: depth_to - depth_from
    description: Optional[str] = None
    
    # Данные ИГЭ из справочника
    ege: GeologyEgeCatalogResponse
    
    # Переопределенные свойства (если есть)
    override_w_tot: Optional[float] = None
    override_rho_dry: Optional[float] = None
    override_lambda_th: Optional[float] = None
    override_lambda_f: Optional[float] = None
    
    # Вычисленные финальные свойства (override или из каталога)
    # Вычисляются в Python коде после получения данных из БД
    final_w_tot: Optional[float] = None
    final_rho_dry: Optional[float] = None
    final_lambda_th: Optional[float] = None
    final_lambda_f: Optional[float] = None
    
    class Config:
        from_attributes = True


class GeologyElementCreate(BaseModel):
    """Создание геологической скважины"""
    name: str
    position_id: Optional[int] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    drilling_date: Optional[str] = None  # YYYY-MM-DD
    ground_water_level: Optional[float] = None
    description: Optional[str] = None


class GeologyElementUpdate(BaseModel):
    """Обновление геологической скважины"""
    name: Optional[str] = None
    position_id: Optional[int] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    drilling_date: Optional[str] = None  # YYYY-MM-DD
    ground_water_level: Optional[float] = None
    description: Optional[str] = None


class GeologyLayerCreate(BaseModel):
    """Создание слоя литологии"""
    element_id: int
    ege_id: int
    depth_from: float
    depth_to: float
    override_w_tot: Optional[float] = None
    override_rho_dry: Optional[float] = None
    override_lambda_th: Optional[float] = None
    override_lambda_f: Optional[float] = None
    description: Optional[str] = None


class GeologyLayerUpdate(BaseModel):
    """Обновление слоя литологии"""
    ege_id: Optional[int] = None
    depth_from: Optional[float] = None
    depth_to: Optional[float] = None
    override_w_tot: Optional[float] = None
    override_rho_dry: Optional[float] = None
    override_lambda_th: Optional[float] = None
    override_lambda_f: Optional[float] = None
    description: Optional[str] = None
    skip_validation: Optional[bool] = False  # Пропустить проверку пересечений (для операций перемещения/изменения мощности)


# ==================== Схемы для осмотров элементов ====================

# DM Inspection - существующие таблицы с дополнениями
class DMInspectionBase(BaseModel):
    """
    Базовая схема для чеклистов осмотров - Data-Driven UI
    Принимает любые параметры чеклиста
    """
    # Обязательные поля для всех чеклистов
    inspectresult: int  # результат осмотра (всегда обязателен)
    note: Optional[str] = None  # примечания
    
    class Config:
        extra = 'allow'  # Разрешаем любые дополнительные поля чеклиста


# Новые схемы только для существующих таблиц с bytea

class DMInspectionCreate(BaseModel):
    """Создание осмотра деформационной марки"""
    cycle_id: int
    marknumber: Optional[int] = Field(0, ge=0, le=5, description="Номер марки")
    markmark: Optional[int] = Field(0, ge=0, le=5, description="Метка марки")
    constructintegrity: Optional[int] = Field(0, ge=0, le=5, description="Целостность конструкции")
    railset: Optional[int] = Field(0, ge=0, le=5, description="Состояние рельсового пути")
    h_railset: Optional[int] = Field(0, ge=0, le=5, description="Можно поставить высокую рейку")
    inspectresult: int = Field(..., ge=0, le=5, description="Общий результат осмотра")
    note: Optional[str] = Field(None, description="Комментарии к осмотру")
    state_id: Optional[str] = Field("exist", description="Статус элемента")
    photos: Optional[bytes] = Field(None, description="Фотографии осмотра")

    @field_validator('photos', mode='before')
    @classmethod
    def validate_photos_input(cls, v):
        if v is None:
            return None
        if isinstance(v, (bytes, bytearray, memoryview)):
            return v
        if isinstance(v, str):
            if ',' in v:
                v = v.split(',', 1)[1]
            try:
                return base64.b64decode(v)
            except Exception:
                raise ValueError("Invalid base64 string for photos")
        return v


class DMInspectionUpdate(BaseModel):
    """Обновление осмотра деформационной марки"""
    marknumber: Optional[int] = Field(None, ge=0, le=5, description="Номер марки")
    markmark: Optional[int] = Field(None, ge=0, le=5, description="Метка марки")
    constructintegrity: Optional[int] = Field(None, ge=0, le=5, description="Целостность конструкции")
    railset: Optional[int] = Field(None, ge=0, le=5, description="Состояние рельсового пути")
    h_railset: Optional[int] = Field(None, ge=0, le=5, description="Можно поставить высокую рейку")
    inspectresult: Optional[int] = Field(None, ge=0, le=5, description="Общий результат осмотра")
    note: Optional[str] = Field(None, description="Комментарии к осмотру")
    photos: Optional[bytes] = Field(None, description="Фотографии осмотра")


class DMInspectionResponse(BaseModel):
    """Ответ с осмотром деформационной марки"""
    inspect_id: int
    element_id: int
    cycle_id: int
    marknumber: Optional[int]
    markmark: Optional[int]
    constructintegrity: Optional[int]
    railset: Optional[int]
    h_railset: Optional[int]
    inspectresult: int
    note: Optional[str]
    state_id: str
    photos: Optional[Union[bytes, str]]

    @field_validator('photos', mode='before')
    @classmethod
    def validate_photos(cls, v):
        if v is None:
            return None
        if isinstance(v, (bytes, bytearray, memoryview)):
            return base64.b64encode(bytes(v)).decode('utf-8')
        return v

    class Config:
        from_attributes = True


class TSInspectionCreate(BaseModel):
    """Создание осмотра термоскважины"""
    cycle_id: int
    namemarked: Optional[int] = Field(0, ge=0, le=5, description="Наличие маркировки")
    protectcase: Optional[int] = Field(0, ge=0, le=5, description="Защитный кожух")
    casecover: Optional[int] = Field(0, ge=0, le=5, description="Крышка кожуха")
    ttcover: Optional[int] = Field(0, ge=0, le=5, description="Крышка термометра")
    insulation: Optional[int] = Field(0, ge=0, le=5, description="Теплоизоляция")
    iceinpipe: Optional[int] = Field(0, ge=0, le=5, description="Лед в трубе")
    waterinpipe: Optional[int] = Field(0, ge=0, le=5, description="Вода в трубе")
    inspectresult: int = Field(..., ge=0, le=5, description="Общий результат осмотра")
    note: Optional[str] = Field(None, description="Комментарии к осмотру")
    state_id: Optional[str] = Field("exist", description="Статус элемента")
    depth: Optional[float] = Field(None, description="Глубина")
    h: Optional[float] = Field(None, description="Высота термотрубки")
    photos: Optional[bytes] = Field(None, description="Фотографии осмотра")

    @field_validator('photos', mode='before')
    @classmethod
    def validate_photos_input(cls, v):
        if v is None:
            return None
        if isinstance(v, (bytes, bytearray, memoryview)):
            return v
        if isinstance(v, str):
            if ',' in v:
                v = v.split(',', 1)[1]
            try:
                return base64.b64decode(v)
            except Exception:
                raise ValueError("Invalid base64 string for photos")
        return v



class TSInspectionUpdate(BaseModel):
    """Обновление осмотра термоскважины"""
    namemarked: Optional[int] = Field(None, ge=0, le=5, description="Наличие маркировки")
    protectcase: Optional[int] = Field(None, ge=0, le=5, description="Защитный кожух")
    casecover: Optional[int] = Field(None, ge=0, le=5, description="Крышка кожуха")
    ttcover: Optional[int] = Field(None, ge=0, le=5, description="Крышка термометра")
    insulation: Optional[int] = Field(None, ge=0, le=5, description="Теплоизоляция")
    iceinpipe: Optional[int] = Field(None, ge=0, le=5, description="Лед в трубе")
    waterinpipe: Optional[int] = Field(None, ge=0, le=5, description="Вода в трубе")
    inspectresult: Optional[int] = Field(None, ge=0, le=5, description="Общий результат осмотра")
    note: Optional[str] = Field(None, description="Комментарии к осмотру")
    depth: Optional[float] = Field(None, description="Глубина")
    h: Optional[float] = Field(None, description="Высота термотрубки")
    photos: Optional[bytes] = Field(None, description="Фотографии осмотра")


class TSInspectionResponse(BaseModel):
    """Ответ с осмотром термоскважины"""
    inspect_id: int
    element_id: int
    cycle_id: int
    namemarked: Optional[int]
    protectcase: Optional[int]
    casecover: Optional[int]
    ttcover: Optional[int]
    insulation: Optional[int]
    iceinpipe: Optional[int]
    waterinpipe: Optional[int]
    inspectresult: int
    note: Optional[str]
    state_id: str
    depth: Optional[float] = None
    h: Optional[float] = None
    photos: Optional[Union[bytes, str]]

    @field_validator('photos', mode='before')
    @classmethod
    def validate_photos(cls, v):
        if v is None:
            return None
        if isinstance(v, (bytes, bytearray, memoryview)):
            return base64.b64encode(bytes(v)).decode('utf-8')
        return v

    class Config:
        from_attributes = True


# RP Inspection - Схемы для осмотров реперов
class RPInspectionCreate(BaseModel):
    """Создание осмотра репера"""
    cycle_id: int
    fence: Optional[int] = Field(0, ge=0, le=5, description="Ограждение")
    protectpit: Optional[int] = Field(0, ge=0, le=5, description="Котлован")
    protectpitcover: Optional[int] = Field(0, ge=0, le=5, description="Крышка котлована")
    protectpipe: Optional[int] = Field(0, ge=0, le=5, description="Защитная труба")
    sealing: Optional[int] = Field(0, ge=0, le=5, description="Наличие сальника")
    mark: Optional[int] = Field(0, ge=0, le=5, description="Марка")
    inspectresult: int = Field(..., ge=0, le=5, description="Общий результат осмотра")
    note: Optional[str] = Field(None, description="Комментарии к осмотру")
    state_id: Optional[str] = Field("exist", description="Статус элемента")
    photos: Optional[bytes] = Field(None, description="Фотографии осмотра")

    @field_validator('photos', mode='before')
    @classmethod
    def validate_photos_input(cls, v):
        if v is None:
            return None
        if isinstance(v, (bytes, bytearray, memoryview)):
            return v
        if isinstance(v, str):
            if ',' in v:
                v = v.split(',', 1)[1]
            try:
                return base64.b64decode(v)
            except Exception:
                raise ValueError("Invalid base64 string for photos")
        return v



class RPInspectionUpdate(BaseModel):
    """Обновление осмотра репера"""
    fence: Optional[int] = Field(None, ge=0, le=5, description="Ограждение")
    protectpit: Optional[int] = Field(None, ge=0, le=5, description="Котлован")
    protectpitcover: Optional[int] = Field(None, ge=0, le=5, description="Крышка котлована")
    protectpipe: Optional[int] = Field(None, ge=0, le=5, description="Защитная труба")
    sealing: Optional[int] = Field(None, ge=0, le=5, description="Наличие сальника")
    mark: Optional[int] = Field(None, ge=0, le=5, description="Марка")
    inspectresult: Optional[int] = Field(None, ge=0, le=5, description="Общий результат осмотра")
    note: Optional[str] = Field(None, description="Комментарии к осмотру")
    photos: Optional[bytes] = Field(None, description="Фотографии осмотра")


class RPInspectionResponse(BaseModel):
    """Ответ с осмотром репера"""
    inspect_id: int
    element_id: int
    cycle_id: int
    fence: Optional[int]
    protectpit: Optional[int]
    protectpitcover: Optional[int]
    protectpipe: Optional[int]
    sealing: Optional[int]
    mark: Optional[int]
    inspectresult: int
    note: Optional[str]
    state_id: str
    photos: Optional[Union[bytes, str]]

    @field_validator('photos', mode='before')
    @classmethod
    def validate_photos(cls, v):
        if v is None:
            return None
        if isinstance(v, (bytes, bytearray, memoryview)):
            return base64.b64encode(bytes(v)).decode('utf-8')
        return v

    class Config:
        from_attributes = True


class DMInspectionBatchItem(DMInspectionCreate):
    element_id: int


class TSInspectionBatchItem(TSInspectionCreate):
    element_id: int


class RPInspectionBatchItem(RPInspectionCreate):
    element_id: int


class UnifiedInspectionBatchCreate(BaseModel):
    dm: List[DMInspectionBatchItem] = []
    ts: List[TSInspectionBatchItem] = []
    rp: List[RPInspectionBatchItem] = []


class UnifiedInspectionResponse(BaseModel):
    """Единый ответ для всех инспекций"""
    metadata: Dict[str, Any]
    states: List[Dict[str, Any]] = []
    dm: List[DMInspectionResponse]
    rp: List[RPInspectionResponse]


# TSS Inspection - Схемы для осмотров TSS
class TSSInspectionCreate(BaseModel):
    """Создание осмотра TSS"""
    cycle_id: int
    meas_density: Optional[float] = Field(None, description="Плотность измерения")
    meas_heigth: Optional[float] = Field(None, description="Высота измерения")
    inspectresult: int = Field(..., ge=0, le=5, description="Общий результат осмотра")
    note: Optional[str] = Field(None, description="Комментарии к осмотру")
    state_id: Optional[str] = Field("exist", description="Статус элемента")
    photos: Optional[bytes] = Field(None, description="Фотографии осмотра")  # Добавлено для совместимости, хотя в SQL нет

    @field_validator('photos', mode='before')
    @classmethod
    def validate_photos_input(cls, v):
        if v is None:
            return None
        if isinstance(v, (bytes, bytearray, memoryview)):
            return v
        if isinstance(v, str):
            if ',' in v:
                v = v.split(',', 1)[1]
            try:
                return base64.b64decode(v)
            except Exception:
                raise ValueError("Invalid base64 string for photos")
        return v


class TSSInspectionUpdate(BaseModel):
    """Обновление осмотра TSS"""
    meas_density: Optional[float] = Field(None, description="Плотность измерения")
    meas_heigth: Optional[float] = Field(None, description="Высота измерения")
    inspectresult: Optional[int] = Field(None, ge=0, le=5, description="Общий результат осмотра")
    note: Optional[str] = Field(None, description="Комментарии к осмотру")
    photos: Optional[bytes] = Field(None, description="Фотографии осмотра")


class TSSInspectionResponse(BaseModel):
    """Ответ с осмотром TSS"""
    inspect_id: int
    element_id: int
    cycle_id: int
    meas_density: Optional[float]
    meas_heigth: Optional[float]
    inspectresult: int
    note: Optional[str]
    state_id: str
    photos: Optional[Union[bytes, str]] = None  # Возможно нет в БД, но для унификации оставим

    @field_validator('photos', mode='before')
    @classmethod
    def validate_photos(cls, v):
        if v is None:
            return None
        if isinstance(v, (bytes, bytearray, memoryview)):
            return base64.b64encode(bytes(v)).decode('utf-8')
        return v

    class Config:
        from_attributes = True


# GGS Inspection - Схемы для осмотров GGS (аналогично RP)
class GGSInspectionCreate(BaseModel):
    """Создание осмотра GGS"""
    cycle_id: int
    namemarked: Optional[int] = Field(0, ge=0, le=5, description="Наличие маркировки")
    protectcase: Optional[int] = Field(0, ge=0, le=5, description="Защитный кожух")
    casecover: Optional[int] = Field(0, ge=0, le=5, description="Крышка кожуха")
    ttcover: Optional[int] = Field(0, ge=0, le=5, description="Крышка термометра")
    insulation: Optional[int] = Field(0, ge=0, le=5, description="Теплоизоляция")
    iceinpipe: Optional[int] = Field(0, ge=0, le=5, description="Лед в трубе")
    waterinpipe: Optional[int] = Field(0, ge=0, le=5, description="Вода в трубе")
    inspectresult: int = Field(..., ge=0, le=5, description="Общий результат осмотра")
    meas: Optional[float] = Field(0, description="Измерение")
    h: Optional[float] = Field(0, description="Высота")
    note: Optional[str] = Field(None, description="Комментарии к осмотру")
    state_id: Optional[str] = Field("exist", description="Статус элемента")
    photos: Optional[bytes] = Field(None, description="Фотографии осмотра")

    @field_validator('photos', mode='before')
    @classmethod
    def validate_photos_input(cls, v):
        if v is None:
            return None
        if isinstance(v, (bytes, bytearray, memoryview)):
            return v
        if isinstance(v, str):
            if ',' in v:
                v = v.split(',', 1)[1]
            try:
                return base64.b64decode(v)
            except Exception:
                raise ValueError("Invalid base64 string for photos")
        return v


class GGSInspectionUpdate(BaseModel):
    """Обновление осмотра GGS"""
    namemarked: Optional[int] = Field(None, ge=0, le=5, description="Наличие маркировки")
    protectcase: Optional[int] = Field(None, ge=0, le=5, description="Защитный кожух")
    casecover: Optional[int] = Field(None, ge=0, le=5, description="Крышка кожуха")
    ttcover: Optional[int] = Field(None, ge=0, le=5, description="Крышка термометра")
    insulation: Optional[int] = Field(None, ge=0, le=5, description="Теплоизоляция")
    iceinpipe: Optional[int] = Field(None, ge=0, le=5, description="Лед в трубе")
    waterinpipe: Optional[int] = Field(None, ge=0, le=5, description="Вода в трубе")
    inspectresult: Optional[int] = Field(None, ge=0, le=5, description="Общий результат осмотра")
    meas: Optional[float] = Field(None, description="Измерение")
    h: Optional[float] = Field(None, description="Высота")
    note: Optional[str] = Field(None, description="Комментарии к осмотру")
    photos: Optional[bytes] = Field(None, description="Фотографии осмотра")


class GGSInspectionResponse(BaseModel):
    """Ответ с осмотром GGS"""
    inspect_id: int
    element_id: int
    cycle_id: int
    namemarked: Optional[int]
    protectcase: Optional[int]
    casecover: Optional[int]
    ttcover: Optional[int]
    insulation: Optional[int]
    iceinpipe: Optional[int]
    waterinpipe: Optional[int]
    inspectresult: int
    meas: Optional[float] = 0.0
    h: Optional[float] = 0.0
    note: Optional[str]
    state_id: str
    photos: Optional[Union[bytes, str]] = None

    @field_validator('photos', mode='before')
    @classmethod
    def validate_photos(cls, v):
        if v is None:
            return None
        if isinstance(v, (bytes, bytearray, memoryview)):
            return base64.b64encode(bytes(v)).decode('utf-8')
        return v

    class Config:
        from_attributes = True


# TSG Inspection - Схемы для осмотров TSG
class TSGInspectionCreate(BaseModel):
    """Создание осмотра TSG"""
    cycle_id: int
    integrity: Optional[int] = Field(0, ge=0, le=5, description="Целостность")
    inspectresult: int = Field(..., ge=0, le=5, description="Общий результат осмотра")
    note: Optional[str] = Field(None, description="Комментарии к осмотру")
    state_id: Optional[str] = Field("exist", description="Статус элемента")
    photos: Optional[bytes] = Field(None, description="Фотографии осмотра")

    @field_validator('photos', mode='before')
    @classmethod
    def validate_photos_input(cls, v):
        if v is None:
            return None
        if isinstance(v, (bytes, bytearray, memoryview)):
            return v
        if isinstance(v, str):
            if ',' in v:
                v = v.split(',', 1)[1]
            try:
                return base64.b64decode(v)
            except Exception:
                raise ValueError("Invalid base64 string for photos")
        return v


class TSGInspectionUpdate(BaseModel):
    """Обновление осмотра TSG"""
    integrity: Optional[int] = Field(None, ge=0, le=5, description="Целостность")
    inspectresult: Optional[int] = Field(None, ge=0, le=5, description="Общий результат осмотра")
    note: Optional[str] = Field(None, description="Комментарии к осмотру")
    photos: Optional[bytes] = Field(None, description="Фотографии осмотра")


class TSGInspectionResponse(BaseModel):
    """Ответ с осмотром TSG"""
    inspect_id: int
    element_id: int
    cycle_id: int
    integrity: Optional[int]
    inspectresult: int
    note: Optional[str]
    state_id: str
    photos: Optional[Union[bytes, str]] = None

    @field_validator('photos', mode='before')
    @classmethod
    def validate_photos(cls, v):
        if v is None:
            return None
        if isinstance(v, (bytes, bytearray, memoryview)):
            return base64.b64encode(bytes(v)).decode('utf-8')
        return v

    class Config:
        from_attributes = True
class DMInspectionBatchItem(DMInspectionCreate):
    element_id: int


class TSInspectionBatchItem(TSInspectionCreate):
    element_id: int


class RPInspectionBatchItem(RPInspectionCreate):
    element_id: int


class TSSInspectionBatchItem(TSSInspectionCreate):
    element_id: int


class GGSInspectionBatchItem(GGSInspectionCreate):
    element_id: int


class TSGInspectionBatchItem(TSGInspectionCreate):
    element_id: int


class UnifiedInspectionBatchCreate(BaseModel):
    dm: List[DMInspectionBatchItem] = []
    ts: List[TSInspectionBatchItem] = []
    rp: List[RPInspectionBatchItem] = []
    tss: List[TSSInspectionBatchItem] = []
    ggs: List[GGSInspectionBatchItem] = []
    tsg: List[TSGInspectionBatchItem] = []


class UnifiedInspectionResponse(BaseModel):
    """Единый ответ для всех инспекций"""
    metadata: Dict[str, Any]
    states: List[Dict[str, Any]] = []
    dm: List[DMInspectionResponse]
    ts: List[TSInspectionResponse]
    rp: List[RPInspectionResponse]
    tss: List[TSSInspectionResponse]
    ggs: List[GGSInspectionResponse]
    tsg: List[TSGInspectionResponse]