import os
import time
import pytest
import requests
from faker import Faker
from clients.api_manager import ApiManager
from entities.user import User
from models.user import UserCreationModel, UserRole
from resources.user_creds import SuperAdminCreds
from utils.data_generator import DataGenerator
from utils.db_client import get_db_session
from utils.db_helpers import DBHelper

# Инициализируем Faker один раз на глобальном уровне
faker = Faker()


# =====================================================================
# СЕТЕВЫЕ СЕССИИ И МЕНЕДЖЕРЫ API
# =====================================================================

@pytest.fixture(scope="session")
def session():
    """Создает единую HTTP-сессию на весь запуск тестов (Session-scope)"""
    http_session = requests.Session()
    yield http_session
    http_session.close()


@pytest.fixture(scope="session")
def api_manager(session):
    """Инициализирует общий менеджер API-клиентов для взаимодействия со стендом"""
    return ApiManager(session)


@pytest.fixture(scope="function")
def unauthenticated_api_manager():
    """
    Неавторизованный менеджер. Создаётся заново на каждый тест (Function-scope).
    Используется для проверки негативных сценариев без токена авторизации.
    """
    with requests.Session() as clean_session:
        yield ApiManager(clean_session)


# =====================================================================
# ГЕНЕРАЦИЯ ДАННЫХ ПОЛЬЗОВАТЕЛЕЙ ЧЕРЕЗ PYDANTIC V2
# =====================================================================

@pytest.fixture(scope="function")
def test_user() -> UserCreationModel:
    """Генерирует гарантированно валидный имейл и случайное имя для строгого бэкенда."""
    import random
    password = DataGenerator.generate_random_password()
    random_id = random.randint(100000, 999999)

    return UserCreationModel(
        email=f"pavelqa{random_id}@gmail.com",       # Только буквы, цифры и @gmail.com
        fullName=faker.name(),                      # Используем faker для красивых имён
        password=password,
        passwordRepeat=password,
        roles=[UserRole.USER]
    )


@pytest.fixture(scope="function")
def creation_user_data(test_user) -> UserCreationModel:
    """
    Админская фикстура данных: берет базового пользователя и добавляет ему
    флаги верификации и блокировки через встроенный метод копирования Pydantic.
    """
    return test_user.model_copy(update={
        "verified": True,
        "banned": False
    })


# =====================================================================
# ФИКСТУРЫ АВТОРИЗАЦИИ И СЛОЖНЫХ РОЛЕЙ (ОБЪЕКТЫ USER)
# =====================================================================

@pytest.fixture(scope="function")
def authenticated_user(api_manager, test_user):
    """
    Быстрая регистрация + Авторизация.
    Регистрирует обычного пользователя на бэкенде и сразу вшивает токен в сессию.
    Возвращает словарь (оставлено для совместимости со старыми тестами курса).
    """
    response = api_manager.auth_api.register_user(test_user).json()

    user_dict = test_user.model_dump()
    user_dict["id"] = response["id"]

    api_manager.auth_api.authenticate(user_dict)
    return user_dict


@pytest.fixture(scope="function")
def authenticated_admin(api_manager):
    """Фикстура для авторизации под SUPER_ADMIN (Данные берутся БЕЗОПАСНО из .env)"""
    admin_email = os.environ.get("SUPER_ADMIN_USERNAME")
    admin_password = os.environ.get("SUPER_ADMIN_PASSWORD")

    if not admin_email or not admin_password:
        raise ValueError("Креды админа не найдены в переменных окружения! Проверь файл .env")

    admin_creds = {
        "email": admin_email,
        "password": admin_password
    }

    response = api_manager.auth_api.login_user(admin_creds, expected_status=200)
    token = response.json()["accessToken"]

    api_manager.movies.session.headers.update({"Authorization": f"Bearer {token}"})

    yield

    if "Authorization" in api_manager.movies.session.headers:
        del api_manager.movies.session.headers["Authorization"]


# =====================================================================
# ФИКСТУРЫ ИЗОЛИРОВАННЫХ СЕССИЙ ДЛЯ СЛОЖНЫХ РОЛЕЙ
# =====================================================================

@pytest.fixture
def super_admin(session):
    """Создает полноценный объект модели User с правами SUPER_ADMIN и авторизует сессию"""
    api_manager = ApiManager(session)
    api_manager.auth_api.authenticate({
        "email": SuperAdminCreds.USERNAME,
        "password": SuperAdminCreds.PASSWORD
    })

    return User(
        email=SuperAdminCreds.USERNAME,
        password=SuperAdminCreds.PASSWORD,
        roles=[UserRole.SUPER_ADMIN]
    )


@pytest.fixture
def common_user(session, creation_user_data):
    """Сценарий: Создание в базе обычного пользователя (USER) и его авторизация"""
    api_manager = ApiManager(session)

    api_manager.auth_api.authenticate({
        "email": SuperAdminCreds.USERNAME,
        "password": SuperAdminCreds.PASSWORD
    })
    api_manager.user_api.create_user(creation_user_data)

    api_manager.auth_api.authenticate({
        "email": creation_user_data.email,
        "password": creation_user_data.password
    })

    return User(
        email=creation_user_data.email,
        password=creation_user_data.password,
        roles=[UserRole.USER]
    )


@pytest.fixture
def admin_user(session, test_user):
    """Практическое задание: Создание и авторизация пользователя с ролью АДМИН"""
    api_manager = ApiManager(session)

    admin_data = test_user.model_copy(update={
        "roles": [UserRole.ADMIN],
        "verified": True,
        "banned": False
    })

    api_manager.auth_api.authenticate({
        "email": SuperAdminCreds.USERNAME,
        "password": SuperAdminCreds.PASSWORD
    })
    api_manager.user_api.create_user(admin_data)

    api_manager.auth_api.authenticate({
        "email": admin_data.email,
        "password": admin_data.password
    })

    return User(
        email=admin_data.email,
        password=admin_data.password,
        roles=[UserRole.ADMIN]
    )


# =====================================================================
# ФИКСТУРЫ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ (DB)
# =====================================================================

@pytest.fixture(scope="function")
def db_session():
    """Создает сессию базы данных на один тест и закрывает ее после"""
    session = get_db_session()
    yield session
    session.close()


@pytest.fixture(scope="function")
def db_helper(db_session):
    """Предоставляет готовый пульт DBHelper в тесты"""
    return DBHelper(db_session)


@pytest.fixture(scope="function")
def created_test_user(db_helper):
    """Автоматически создает случайного юзера перед тестом и удаляет его после"""
    user_data = DataGenerator.generate_user_data()
    user = db_helper.create_test_user(user_data)

    yield user

    if db_helper.get_user_by_id(user.id):
        db_helper.delete_user(user)