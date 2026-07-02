# conftest.py
import requests
import pytest
from clients.api_manager import ApiManager
from utils.data_generator import DataGenerator
from entities.user import User
from resources.user_creds import SuperAdminCreds


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

@pytest.fixture
def user_session():
    user_pool = []

    def _create_user_session():
        session = requests.Session()
        user_api_manager = ApiManager(session)
        user_pool.append(user_api_manager)
        return user_api_manager

    yield _create_user_session

    for user_api in user_pool:
        user_api.close_session()

@pytest.fixture
def super_admin(user_session):
    new_session = user_session()

    admin_user = User(
        email=SuperAdminCreds.USERNAME,
        password=SuperAdminCreds.PASSWORD,
        roles=["[SUPER_ADMIN]"],
        api=new_session
    )

    admin_creds = {
        "email": admin_user.email,
        "password": admin_user.password
    }
    admin_user.api.auth_api.authenticate(admin_creds)

    return admin_user

@pytest.fixture(scope="function")
def creation_user_data(test_user):
    """Готовит расширенные данные для создания юзера через админку"""
    updated_data = test_user.copy()

    updated_data.update({
        "verified": True,
        "banned": False
    })

    return updated_data