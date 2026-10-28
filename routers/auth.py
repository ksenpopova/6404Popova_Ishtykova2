from fastapi import APIRouter
from schemas import UserAuth

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
def register(user: UserAuth):
    # Упрощенная логика (без БД и хэширования, т.к. без доп. задания)
    return {"message": "Пользователь успешно зарегистрирован", "username": user.username}

@router.post("/login")
def login(user: UserAuth):
    # Упрощенный логин
    if user.username == "admin" and user.password == "admin":
        return {"message": "Успешный вход", "token": "dummy-auth-token"}
    return {"message": "Неверный логин или пароль"}