import pytest
from pydantic import ValidationError
from models.user import UserCreationModel, UserRole, RegisterUserResponseModel

# =====================================================================
# УЧЕБНЫЕ ТЕСТЫ ДЛЯ ПРОВЕРКИ ЛОГИКИ МОДЕЛЕЙ PYDANTIC V2
# =====================================================================

def test_password_mismatch_validation(test_user):
    """Тест проверяет работу кастомного валидатора: несовпадающие пароли должны вызывать ошибку"""
    # 1. Сгружаем все данные готового юзера из фикстуры в словарь
    user_data = test_user.model_dump()

    # 2. Меняем ТОЛЬКО то, что проверяем в этом тесте, ломаем повтор пароля
    user_data["passwordRepeat"] = "WrongRepeat456"

    # 3. Проверяем, что Pydantic ругнётся именно на пароли
    with pytest.raises(ValidationError) as exc_info:
        UserCreationModel(**user_data)

    print("\n\n" + "=" * 50)
    print("ПЕРЕХВАЧЕНА ОШИБКА СОВПАДЕНИЯ ПАРОЛЕЙ:")
    print("=" * 50)
    print(exc_info.value)
    print("=" * 50)


def test_invalid_date_format_from_api():
    """Тест проверяет валидацию даты: бэк не может прислать текст вместо ISO формата"""
    # КОММЕНТАРИЙ ДЛЯ СЕБЯ: Здесь Билдер (test_user) НЕ используется сознательно.
    # Этот тест проверяет совершенно другую модель, RegisterUserResponseModel (ответ от API).
    # Мы симулируем исключительно сломанный, хардкодный JSON от бэкенда, чтобы проверить валидатор даты.
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


def test_api_registration_response_validation(test_user):
    """
    Симуляция проверки ответа реального API через RegisterUserResponseModel.
    """
    # МЕНЯЕМ НА БИЛДЕР: Чтобы тест не упал при изменении полей на бэке,
    # подтягиваем email и fullName динамически из фикстуры test_user
    mock_api_response = {
        "id": "abracadabra1234-2-2-2",
        "email": test_user.email,
        "fullName": test_user.fullName,
        "verified": False,
        "banned": False,
        "roles": ["USER"],
        "createdAt": "2020-01-08T12:00:56.789Z"
    }

    # Валидируем пришедшую структуру одной строкой через Pydantic
    validated_response = RegisterUserResponseModel(**mock_api_response)

    # Проверяем бизнес-логику: почта в ответе совпадает с отправленной
    assert validated_response.email == test_user.email, "Email в ответе API не совпадает с исходным!"