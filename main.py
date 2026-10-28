from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models

# Импорт роутеров (если каких-то файлов еще нет в папке routers, закомментируйте их)
from routers import auth, clients, claims #, agents, contracts, products

# Автоматическое создание таблиц в БД (если они еще не созданы)
models.Base.metadata.create_all(bind=engine)

# Инициализация приложения с настройками для Swagger-документации
app = FastAPI(
    title="Insurance System API",
    description="REST API для управления распределенной системой страховой компании",
    version="1.0.0"
)

# Настройка CORS (разрешает сторонним сайтам делать запросы к вашему API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router, prefix="/auth", tags=["Аутентификация"])
app.include_router(clients.router, prefix="/clients", tags=["Клиенты"])
app.include_router(claims.router, prefix="/claims", tags=["Страховые случаи"])

# Задел на будущее (подключите, когда создадите эти файлы в папке routers)
# app.include_router(agents.router, prefix="/agents", tags=["Агенты"])
# app.include_router(contracts.router, prefix="/contracts", tags=["Договоры"])
# app.include_router(products.router, prefix="/products", tags=["Страховые продукты"])

@app.get("/", tags=["Служебные"])
def root():
    return {"message": "Добро пожаловать в API Страховой компании. Документация доступна по адресу /docs"}