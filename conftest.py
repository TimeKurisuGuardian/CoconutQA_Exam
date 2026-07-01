# conftest.py
import requests
import pytest
from clients.api_manager import ApiManager
from utils.data_generator import DataGenerator


# Главный менеджер (Общий)
@pytest.fixture(scope="session")
def session():
    http_session = requests.Session()
    yield http_session
    http_session.close()


@pytest.fixture(scope="session")
def api_manager(session):
    return ApiManager(session)


# ВАРИАНТ 2: Чистый, неавторизованный менеджер (для тестов без токена)
@pytest.fixture(scope="function")  # Создаётся КАЖДЫЙ РАЗ заново, с чистыми заголовками!
def unauthenticated_api_manager():
    with requests.Session() as clean_session:
        yield ApiManager(clean_session)


# Фикстура генерации данных
@pytest.fixture(scope="function")
def test_user():
    password = DataGenerator.generate_random_password()
    return {
        "email": DataGenerator.generate_random_email(),
        "fullName": DataGenerator.generate_random_name(),
        "password": password,
        "passwordRepeat": password,
        "roles": ["USER"]
    }


# Фикстура, которая регистрирует И СРАЗУ авторизует сессию
@pytest.fixture(scope="function")
def authenticated_user(api_manager, test_user):
    # 1. Регистрируем пользователя
    response = api_manager.auth_api.register_user(test_user).json()
    test_user["id"] = response["id"]

    # 2. Сразу вызываем метод аутентификации, чтобы вшить токен в сессию
    api_manager.auth_api.authenticate(test_user)

    # 3. Возвращаем словарь с моими данными(включая айди)
    return test_user


@pytest.fixture(scope="function")
def authenticated_admin(api_manager):
    """Фикстура для авторизации под SUPER_ADMIN (использует креды из ТЗ)"""
    admin_creds = {
        "email": "api1@gmail.com",
        "password": "asdqwe123Q"
    }

    response = api_manager.auth_api.login_user(admin_creds, expected_status=201)
    token = response.json()["accessToken"]

    # Вшиваем токен админа в заголовки сессии фильмов
    api_manager.movies.session.headers.update({"Authorization": f"Bearer {token}"})

    yield

    # После теста очищаем заголовок авторизации
    if "Authorization" in api_manager.movies.session.headers:
        del api_manager.movies.session.headers["Authorization"]