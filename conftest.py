import requests
import pytest
from clients.api_manager import ApiManager
from utils.data_generator import DataGenerator
from entities.user import User
from resources.user_creds import SuperAdminCreds
# Полностью перешли на единый Enum из нашей Pydantic модели, старый Roles удален
from models.user import UserCreationModel, UserRole
import time
import os

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


@pytest.fixture
def user_session():
    """Пул изолированных сессий для реализации параллельных сессий пользователей в тестах"""
    user_pool = []

    def _create_user_session():
        session = requests.Session()
        user_api_manager = ApiManager(session)
        user_pool.append(user_api_manager)
        return user_api_manager

    yield _create_user_session

    # Пост-условие: закрываем все созданные сессии пользователей
    for user_api in user_pool:
        user_api.close_session()


@pytest.fixture
def super_admin(user_session):
    """Создает полноценный объект модели User с правами SUPER_ADMIN на выделенной сессии"""
    new_session = user_session()

    super_admin_obj = User(
        email=SuperAdminCreds.USERNAME,
        password=SuperAdminCreds.PASSWORD,
        roles=[UserRole.SUPER_ADMIN],
        api=new_session
    )

    # Проходим аутентификацию на сервере для получения Bearer токена
    super_admin_obj.api.auth_api.authenticate({
        "email": SuperAdminCreds.USERNAME,
        "password": SuperAdminCreds.PASSWORD
    })
    return super_admin_obj


@pytest.fixture
def common_user(user_session, super_admin, creation_user_data):
    """Сценарий: Супер-админ создает в базе обычного пользователя (USER), а тот авторизуется"""
    new_session = user_session()

    # Инициализируем объект нашей сущности User
    user = User(
        email=creation_user_data.email,
        password=creation_user_data.password,
        roles=[UserRole.USER],
        api=new_session
    )

    # Супер-админ отправляет запрос на создание этого пользователя на бэкенде
    super_admin.api.user_api.create_user(creation_user_data)

    # Сам созданный пользователь логинится в свою сессию
    user.api.auth_api.authenticate({
        "email": user.email,
        "password": user.password
    })
    return user


@pytest.fixture
def admin_user(user_session, super_admin, test_user):
    """Практическое задание: Создание и авторизация пользователя с ролью АДМИН"""
    new_session = user_session()

    # С помощью Pydantic v2 меняем базовую роль на ADMIN
    admin_data = test_user.model_copy(update={
        "roles": [UserRole.ADMIN],
        "verified": True,
        "banned": False
    })

    user = User(
        email=admin_data.email,
        password=admin_data.password,
        roles=[UserRole.ADMIN],
        api=new_session
    )

    # Создаем админа в базе руками супер-администратора
    super_admin.api.user_api.create_user(admin_data)

    # Авторизуем админа
    user.api.auth_api.authenticate({
        "email": user.email,
        "password": user.password
    })
    return user