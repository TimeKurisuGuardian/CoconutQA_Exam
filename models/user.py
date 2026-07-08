import datetime
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from typing import List, Optional
from enum import Enum

# =====================================================================
# РОЛЕВАЯ МОДЕЛЬ (ENUM)
# =====================================================================
class UserRole(str, Enum):
    """
    Перечисление доступных ролей в системе.
    Наследование от str позволяет Pydantic v2 автоматически сериализовать 
    объекты Enum в обычные строки при отправке JSON-запросов на бэкенд.
    """
    USER = "USER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


# =====================================================================
# МОДЕЛЬ ДЛЯ ОТПРАВКИ ЗАПРОСА (РЕГИСТРАЦИЯ / СОЗДАНИЕ)
# =====================================================================
class UserCreationModel(BaseModel):
    """
    Модель валидации входящих данных для создания нового пользователя.
    Используется в фикстурах и тестах для генерации корректных payload запросов.
    """
    email: str = Field(..., description="Электронная почта пользователя")
    fullName: str = Field(..., min_length=1, max_length=100, description="Полное имя")
    password: str = Field(..., min_length=8, max_length=20, description="Пароль (от 8 до 20 символов)")
    passwordRepeat: str = Field(..., min_length=8, max_length=20, description="Повтор пароля для сверки")
    roles: List[UserRole] = [UserRole.USER]  # По умолчанию создается обычный юзер
    verified: Optional[bool] = None
    banned: Optional[bool] = None

    @field_validator("passwordRepeat")
    def check_password_repeat(cls, value: str, info: ValidationInfo) -> str:
        """Кастомный валидатор для сверки основного и повторного паролей."""
        if "password" in info.data and value != info.data["password"]:
            raise ValueError("Пароли не совпадают! Проверьте ввод.")
        return value


# =====================================================================
# МОДЕЛЬ ДЛЯ ВАЛИДАЦИИ ОТВЕТА СЕРВЕРА
# =====================================================================
class RegisterUserResponseModel(BaseModel):
    """
    Модель сквозной автоматической валидации ответов бэкенда учебного стенда.
    Проверяет структуру, типы данных и корректность ключевых полей одной строкой.
    """
    id: str = Field(..., description="Уникальный UUID пользователя, сгенерированный сервером")
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", description="Валидный Email адрес")
    fullName: str = Field(..., min_length=1, max_length=100, description="Полное имя")
    verified: bool = Field(..., description="Статус верификации аккаунта")
    banned: Optional[bool] = Field(default=None, description="Статус блокировки аккаунта (опционально)")
    roles: List[UserRole] = Field(..., description="Список присвоенных ролей")
    createdAt: str = Field(..., description="Дата создания аккаунта бэкендом")

    @field_validator("createdAt")
    def validate_created_at(cls, value: str) -> str:
        """Кастомный валидатор проверки формата времени создания аккаунта."""
        try:
            # Проверяем, что строка свободно конвертируется в строгий datetime формат ISO 8601
            datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("Некорректный формат даты от бэкенда! Ожидается ISO 8601")
        return value