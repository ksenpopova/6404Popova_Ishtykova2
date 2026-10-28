from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Импорт ваших настроек БД
from database import engine
import models

# Импорт всех роутеров
from routers import auth, clients, claims, agents, contracts, products, properties

# Автоматическое создание таблиц в БД
models.Base.metadata.create_all(bind=engine)

# Инициализация приложения с настройками для Swagger-документации
app = FastAPI(
    title="Insurance System API",
    description="REST API для управления распределенной системой страховой компании",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение всех роутеров
app.include_router(auth.router, prefix="/auth", tags=["Аутентификация"])
app.include_router(clients.router, prefix="/clients", tags=["Клиенты"])
app.include_router(claims.router, prefix="/claims", tags=["Страховые случаи"])
app.include_router(agents.router, prefix="/agents", tags=["Агенты"])
app.include_router(contracts.router, prefix="/contracts", tags=["Договоры"])
app.include_router(products.router, prefix="/products", tags=["Страховые продукты"])
app.include_router(properties.router, prefix="/properties", tags=["Имущество"])

@app.get("/", tags=["Служебные"])
def root():
    return {"message": "Добро пожаловать в API Страховой компании. Документация доступна по адресу /docs"}