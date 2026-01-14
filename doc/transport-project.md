Результаты подготовки системы авторизации
Система авторизации проекта cloud.entro.pro успешно извлечена и подготовлена к переносу. Все необходимые файлы собраны в директории /opt/cloud.entro.pro/auth_export/.

Состав извлеченных компонентов
Backend
Маршруты: auth_routes.py
Модели и Схемы: models.py, schemas.py, database.py
Безопасность: auth_utils.py, auth_dependencies.py
Сервисы: email_service.py
Frontend
Сервисы: authService.ts, axiosInstance.ts
Контекст: AuthContext.tsx
Страницы: Полный набор страниц (Login, Register, VerifyEmail, ForgotPassword и др.)
База данных
SQL: init_auth.sql (создание таблиц users и audit_logs)
Инструкции по развертыванию на новом VPS
База данных: Выполните скрипт db/init_auth.sql в вашей PostgreSQL.
Переменные окружения: Установите следующие переменные в вашем .env:
JWT_SECRET_KEY (сгенерируйте новый: openssl rand -hex 32)
Параметры подключения к БД (POSTGRES_USER, POSTGRES_PASSWORD и т.д.)
Настройки SMTP для почты
Backend: Скопируйте файлы в аналогичные директории вашего FastAPI проекта и подключите auth_router в main.py.
Frontend: Скопируйте файлы сервисов, контекста и страниц. Убедитесь, что axiosInstance настроен на правильный URL вашего нового API.
Директорию /opt/cloud.entro.pro/auth_export/ можно упаковать в ZIP для удобства скачивания.