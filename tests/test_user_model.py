import pytest
from pydantic import ValidationError
from models.user import UserCreationModel, UserRole, RegisterUserResponseModel

# =====================================================================
# УЧЕБНЫЕ ТЕСТЫ ДЛЯ ПРОВЕРКИ ЛОГИКИ МОДЕЛЕЙ PYDANTIC V2
# =====================================================================

def test_password_mismatch_validation():
    """Тест проверяет работу кастомного валидатора: несовпадающие пароли должны вызывать ошибку"""
    bad_passwords = {
        "email": "paavto@qa.pro",
        "fullName": "Па Автоматизатор",
        "password": "Password123",
        "passwordRepeat": "WrongRepeat456",  # Специально пишем разные пароли
        "roles": ["USER"]
    }

    # Ждем, что Pydantic выплюнет ValidationError
    with pytest.raises(ValidationError) as exc_info:
        UserCreationModel(**bad_passwords)

    print("\n\n" + "="*50)
    print("ПЕРЕХВАЧЕНА ОШИБКА СОВПАДЕНИЯ ПАРОЛЕЙ:")
    print("="*50)
    print(exc_info.value)
    print("="*50)


def test_invalid_date_format_from_api():
    """Тест проверяет валидацию даты: бэк не может прислать текст вместо ISO формата"""
    bad_api_data = {
        "id": "user_id_1",
        "email": "paavto@qa.pro",
        "fullName": "Па Глава",
        "verified": True,
        "banned": False,
        "roles": ["USER"],
        "createdAt": "сегодня после душа"  # Некорректный формат даты
    }

    with pytest.raises(ValidationError) as exc_info:
        RegisterUserResponseModel(**bad_api_data)

    print("\n\n" + "="*50)
    print("БЭКЕНД ПРИСЛАЛ НЕКОРРЕКТНЫЙ ФОРМАТ ДАТЫ:")
    print("="*50)
    print(exc_info.value)
    print("="*50)


def test_api_registration_response_validation():
    """
    Симуляция проверки ответа реального API через RegisterUserResponseModel.
    Тест полностью изолирован и не требует внешних фикстур.
    """
    # 1. Создаем эталонный локальный объект запроса
    local_user = UserCreationModel(
        email="pa_test@gmail.com",
        fullName="Па Тестовый",
        password="Password123",
        passwordRepeat="Password123",
        roles=[UserRole.USER]
    )

    # 2. Имитируем идеальный ответ, который как будто прислал сервер Сайнскопа
    mock_api_response = {
        "id": "abracadabra1234-2-2-2",
        "email": local_user.email,
        "fullName": local_user.fullName,
        "verified": False,
        "banned": False,
        "roles": ["USER"],
        "createdAt": "2020-01-08T12:00:56.789Z"  # Строгий ISO формат
    }

    # 3. Валидируем пришедшую структуру одной строкой через Pydantic
    validated_response = RegisterUserResponseModel(**mock_api_response)

    # 4. Проверяем бизнес-логику: почта в ответе совпадает с отправленной
    assert validated_response.email == local_user.email, "Email в ответе API не совпадает с исходным!"

    print("\n\n" + "="*50)
    print("API ОТВЕТ УСПЕШНО ВАЛИДИРОВАН МОДЕЛЬЮ PYDANTIC!")
    print(f"ID нового юзера: {validated_response.id}")
    print(f"Дата создания: {validated_response.createdAt}")
    print("="*50)