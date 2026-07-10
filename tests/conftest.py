import requests
import pytest
from clients.api_manager import ApiManager
from utils.data_generator import DataGenerator
from entities.user import User
from resources.user_creds import SuperAdminCreds
from models.user import UserCreationModel, UserRole
import time
import os
from utils.db_client import get_db_session
from utils.db_helpers import DBHelper

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
    """
    Базовая фикстура: Генерирует случайные валидные данные нового пользователя.
    Возвращает строгий объект Pydantic модели UserCreationModel.
    """
    password = DataGenerator.generate_random_password()
    unique_suffix = int(time.time())  # Таймстамп для уникальности
    return UserCreationModel(
        email=f"pavel_{unique_suffix}_{DataGenerator.generate_random_email()}",  # Уникализировали почту!
        fullName=DataGenerator.generate_random_name(),
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
    # Наш CustomRequester сам поймет, что пришла модель, и переведет её в нужный формат
    response = api_manager.auth_api.register_user(test_user).json()

    # Из ответа вытаскиваем сгенерированный сервером id
    user_dict = test_user.model_dump()
    user_dict["id"] = response["id"]

    # Вшиваем токен авторизации в сессию
    api_manager.auth_api.authenticate(user_dict)
    return user_dict


@pytest.fixture(scope="function")
def authenticated_admin(api_manager):
    """Фикстура для авторизации под SUPER_ADMIN (Данные берутся БЕЗОПАСНО из .env)"""

    # Забираем переменные окружения, которые загружает pytest-dotenv или твоя система
    admin_email = os.environ.get("SUPER_ADMIN_USERNAME")
    admin_password = os.environ.get("SUPER_ADMIN_PASSWORD")

    # Перестраховка: если .env не прочитался, тест упадет с понятной ошибкой
    if not admin_email or not admin_password:
        raise ValueError("Креды админа не найдены в переменных окружения! Проверь файл .env")

    admin_creds = {
        "email": admin_email,
        "password": admin_password
    }

    response = api_manager.auth_api.login_user(admin_creds, expected_status=201)
    token = response.json()["accessToken"]

    # Вшиваем токен админа в заголовки сессии фильмов
    api_manager.movies.session.headers.update({"Authorization": f"Bearer {token}"})

    yield

    # После теста очищаем заголовок авторизации
    if "Authorization" in api_manager.movies.session.headers:
        del api_manager.movies.session.headers["Authorization"]

# =====================================================================
# ФИКСТУРЫ ИЗОЛИРОВАННЫХ СЕССИЙ ДЛЯ СЛОЖНЫХ РОЛЕЙ
# =====================================================================

@pytest.fixture
def super_admin(session):
    """Создает полноценный объект модели User с правами SUPER_ADMIN и авторизует сессию"""
    # Шаг 1: Инициализируем менеджер API на базе общей сессии
    api_manager = ApiManager(session)

    # Шаг 2: Проходим аутентификацию под супер-админом
    api_manager.auth_api.authenticate({
        "email": SuperAdminCreds.USERNAME,
        "password": SuperAdminCreds.PASSWORD
    })

    # Шаг 3: Создаем чистую сущность пользователя (теперь без передачи api!)
    super_admin_obj = User(
        email=SuperAdminCreds.USERNAME,
        password=SuperAdminCreds.PASSWORD,
        roles=[UserRole.SUPER_ADMIN]
    )
    return super_admin_obj


@pytest.fixture
def common_user(session, creation_user_data):
    """Сценарий: Создание в базе обычного пользователя (USER) и его авторизация"""
    api_manager = ApiManager(session)

    # Шаг 1: Супер-админ (используем его креды напрямую через константы) создает пользователя на бэкенде
    # Сначала авторизуем сессию как супер-админ, чтобы создать юзера
    api_manager.auth_api.authenticate({
        "email": SuperAdminCreds.USERNAME,
        "password": SuperAdminCreds.PASSWORD
    })
    api_manager.user_api.create_user(creation_user_data)

    # Шаг 2: Авторизуем эту же сессию под только что созданным пользователем
    api_manager.auth_api.authenticate({
        "email": creation_user_data.email,
        "password": creation_user_data.password
    })

    # Шаг 3: Возвращаем чистый объект сущности пользователя
    user = User(
        email=creation_user_data.email,
        password=creation_user_data.password,
        roles=[UserRole.USER]
    )
    return user


@pytest.fixture
def admin_user(session, test_user):
    """Практическое задание: Создание и авторизация пользователя с ролью АДМИН"""
    api_manager = ApiManager(session)

    # Шаг 1: Подготавливаем данные админа через Pydantic v2
    admin_data = test_user.model_copy(update={
        "roles": [UserRole.ADMIN],
        "verified": True,
        "banned": False
    })

    # Шаг 2: Авторизуемся супер-админом и создаем нового админа в базе
    api_manager.auth_api.authenticate({
        "email": SuperAdminCreds.USERNAME,
        "password": SuperAdminCreds.PASSWORD
    })
    api_manager.user_api.create_user(admin_data)

    # Шаг 3: Переавторизуем сессию под новым админом
    api_manager.auth_api.authenticate({
        "email": admin_data.email,
        "password": admin_data.password
    })

    # Шаг 4: Возвращаем объект сущности
    user = User(
        email=admin_data.email,
        password=admin_data.password,
        roles=[UserRole.ADMIN]
    )
    return user

# --- НОВОЕ ---
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