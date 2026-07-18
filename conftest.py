import os
import time
import pytest
import requests
from faker import Faker
from playwright.sync_api import sync_playwright

from clients.api_manager import ApiManager
from entities.user import User
from models.user import UserCreationModel, UserRole
from resources.user_creds import SuperAdminCreds
from utils.data_generator import DataGenerator
from utils.db_client import get_db_session
from utils.db_helpers import DBHelper
from utils.tools import Tools

faker = Faker()
DEFAULT_UI_TIMEOUT = 15000


# =====================================================================
# СЕТЕВЫЕ СЕССИИ И МЕНЕДЖЕРЫ API
# =====================================================================

@pytest.fixture(scope="session")
def session():
    """Инициализирует единую HTTP-сессию для всех тестов в рамках сессии."""
    http_session = requests.Session()
    yield http_session
    http_session.close()


@pytest.fixture(scope="session")
def api_manager(session):
    """Предоставляет общий менеджер API-клиентов."""
    return ApiManager(session)


@pytest.fixture(scope="function")
def unauthenticated_api_manager():
    """
    Предоставляет неавторизованный менеджер API для проверки
    негативных сценариев без токена доступа.
    """
    with requests.Session() as clean_session:
        yield ApiManager(clean_session)


# =====================================================================
# ГЕНЕРАЦИЯ ДАННЫХ ПОЛЬЗОВАТЕЛЕЙ
# =====================================================================

@pytest.fixture(scope="function")
def test_user() -> UserCreationModel:
    """Генерирует валидные данные пользователя для регистрации."""
    import random
    password = DataGenerator.generate_random_password()
    random_id = random.randint(100000, 999999)

    return UserCreationModel(
        email=f"pavelqa{random_id}@gmail.com",
        fullName=faker.name(),
        password=password,
        passwordRepeat=password,
        roles=[UserRole.USER]
    )


@pytest.fixture(scope="function")
def creation_user_data(test_user) -> UserCreationModel:
    """Модифицирует базовые данные пользователя, устанавливая флаги верификации."""
    return test_user.model_copy(update={
        "verified": True,
        "banned": False
    })


# =====================================================================
# ФИКСТУРЫ АВТОРИЗАЦИИ И РОЛЕЙ
# =====================================================================

@pytest.fixture(scope="function")
def authenticated_user(api_manager, test_user):
    """Выполняет регистрацию и авторизацию стандартного пользователя."""
    response = api_manager.auth_api.register_user(test_user).json()

    user_dict = test_user.model_dump()
    user_dict["id"] = response["id"]

    api_manager.auth_api.authenticate(user_dict)
    return user_dict


@pytest.fixture(scope="function")
def authenticated_admin(api_manager):
    """Выполняет авторизацию под учетной записью SUPER_ADMIN на основе конфигурации .env."""
    admin_email = os.environ.get("SUPER_ADMIN_USERNAME")
    admin_password = os.environ.get("SUPER_ADMIN_PASSWORD")

    if not admin_email or not admin_password:
        raise ValueError("Учетные данные администратора не найдены в переменных окружения.")

    admin_creds = {
        "email": admin_email,
        "password": admin_password
    }

    # МЕНЯЕМ ТУТ: разрешаем бэкенду возвращать и 200, и 201
    response = api_manager.auth_api.login_user(admin_creds, expected_status=[200, 201])
    token = response.json()["accessToken"]

    api_manager.movies.session.headers.update({"Authorization": f"Bearer {token}"})

    yield

    if "Authorization" in api_manager.movies.session.headers:
        del api_manager.movies.session.headers["Authorization"]


@pytest.fixture
def super_admin(session):
    """Создает объект пользователя с правами SUPER_ADMIN и авторизует сессию."""
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
    """Создает в системе стандартного пользователя и авторизует текущую сессию."""
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
    """Создает в системе пользователя с ролью ADMIN и авторизует текущую сессию."""
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
# ФИКСТУРЫ РАБОТЫ С БАЗОЙ ДАННЫХ
# =====================================================================

@pytest.fixture(scope="function")
def db_session():
    """Инициализирует и изолирует сессию базы данных на уровне теста."""
    session = get_db_session()
    yield session
    session.close()


@pytest.fixture(scope="function")
def db_helper(db_session):
    """Предоставляет экземпляр класса DBHelper для работы с БД."""
    return DBHelper(db_session)


@pytest.fixture(scope="function")
def created_test_user(db_helper):
    """Генерирует тестового пользователя в БД с последующим удалением после теста."""
    user_data = DataGenerator.generate_user_data()
    user = db_helper.create_test_user(user_data)

    yield user

    if db_helper.get_user_by_id(user.id):
        db_helper.delete_user(user)


# =====================================================================
# UI И PLAYWRIGHT ФИКСТУРЫ
# =====================================================================

@pytest.fixture(scope="session")
def browser():
    """Инициализирует экземпляр браузера Chromium на время сессии тестов."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser):
    """Создает изолированный контекст браузера и сохраняет артефакты трассировки."""
    context = browser.new_context()
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    context.set_default_timeout(DEFAULT_UI_TIMEOUT)
    yield context

    # Генерация пути через перенесенный класс Tools
    trace_path = Tools.files_dir(nested_directory="traces", filename=f"trace_{Tools.get_timestamp()}.zip")

    context.tracing.stop(path=str(trace_path))
    context.close()


@pytest.fixture(scope="function")
def page(context):
    """Предоставляет новую страницу в рамках изолированного контекста."""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="function")
def ui_registered_user(api_manager, test_user):
    """Регистрирует пользователя через API бэкенда для использования в UI сценариях."""
    api_manager.auth_api.register_user(test_user)
    return test_user