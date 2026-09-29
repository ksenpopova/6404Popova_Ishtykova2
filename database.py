from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Строка подключения к PostgreSQL (замените логин/пароль на свои)
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:1234@localhost:5432/insurance_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()