import time
import pytest
from clients.api_manager import ApiManager
from models.user import RegisterUserResponseModel


def test_register_user(api_manager: ApiManager, test_user):
    """
    Позитивный тест на базовую регистрацию пользователя.
    Использует Pydantic-модель ответа для автоматической сквозной валидации
    всех полей, типов данных и формата даты бэкенда.
    """
    # 1. Отправляем модель test_user напрямую (наш CustomRequester сам превратит её в JSON)
    response = api_manager.auth_api.register_user(user_data=test_user)

    # 2. ДЕСЕРИАЛИЗАЦИЯ: Натягиваем сырой JSON-ответ на строгую модель ответа.
    #    Здесь Pydantic автоматически проверяет структуру, типы и формат даты ISO 8601.
    register_user_response = RegisterUserResponseModel(**response.json())

    # 3. Проверяем бизнес-логику: зарегистрировалась именно та почта, которую мы отправляли
    assert register_user_response.email == test_user.email, "Email в ответе API не совпадает с отправленным"


def test_full_auth_and_profile_flow(api_manager, faker):
    """
    Интеграционный тест полного цикла (End-to-End).
    Эмулирует реальный путь пользователя: Регистрация -> Логин (Аутентификация) ->
    Проверка доступа к защищенному эндпоинту (Фильмы) по сгенерированному токену.
    """
    # Генерация уникальных случайных данных для теста
    username = faker.user_name()
    password = "ValidPassword123"
    email = f"user_{int(time.time())}@example.com"
    name = faker.name()

    # Полезная нагрузка для создания профиля
    user_payload = {
        "email": email,
        "username": username,
        "password": password,
        "passwordRepeat": password,
        "fullName": name
    }

    # ШАГ 1: Регистрация нового аккаунта в системе через API
    api_manager.auth_api.register_user(user_payload, expected_status=201)

    # ШАГ 2: Аутентификация. Метод authenticate() не просто логинится,
    # а перехватывает токен из ответа и жестко вшивает его в headers текущей сессии requests!
    login_payload = {
        "email": email,
        "password": password
    }
    api_manager.auth_api.authenticate(login_payload)

    # ШАГ 3: Проверка авторизации. Стучимся в защищенную ручку фильмов.
    # Если токен не вшился или слетел, то сервер вернет 401/403 и тест упадет здесь.
    movies_response = api_manager.movies.get_movies(expected_status=200)

    # Дополнительная проверка структуры ответа ручки фильмов
    assert "movies" in movies_response.json(), "Ключ 'movies' отсутствует в ответе сервера"


def test_login_with_invalid_credentials(api_manager, faker):
    """
    Негативный тест на аутентификацию.
    Проверяет, что система безопасности бэкенда корректно отрабатывает
    и возвращает ошибку 401 Unauthorized при попытке входа с фейковыми данными.
    """
    # Генерируем случайную грязь, которой гарантированно нет в базе данных
    invalid_payload = {
        "email": f"fake_{int(time.time())}@invalid.com",  # Используем email, так как бэк ждет его для входа
        "password": faker.password()
    }

    # Отправляем запрос и проверяем, что бэкенд выплюнул строгую 401 ошибку
    api_manager.auth_api.login_user(invalid_payload, expected_status=401)