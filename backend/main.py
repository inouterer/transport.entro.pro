import os
import uvicorn
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth_routes import auth_router
from core.database import engine, Base

# Настройка логирования
structlog.configure()
logger = structlog.get_logger()

# Создание таблиц при запуске (если не используется Alembic)
# В продакшене лучше использовать миграции
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Transport Control Service API",
    description="API для сервиса контроля пассажирских перевозок",
    version="1.0.0"
)

# Настройка CORS
origins = os.environ.get("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Welcome to Transport Control Service API",
        "status": "online"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
