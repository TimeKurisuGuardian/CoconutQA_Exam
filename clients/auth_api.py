from custom_requester.custom_requester import CustomRequester
from config.base_urls import AUTH_BASE_URL

# Константы эндпоинтов для централизованного управления маршрутами
LOGIN = '/login'
REGISTER = '/register'
LOGOUT = '/logout'


class AuthApi(CustomRequester):
    """
    API-клиент для работы с сервисом аутентификации и авторизации (Auth API).
    Наследует базовый функционал отправки запросов от класса CustomRequester.
    """

    def __init__(self, session):
        # Передаем общую сессию и базовый URL аутентификации в конструктор родительского класса
        super().__init__(session=session, base_url=AUTH_BASE_URL)

    def register_user(self, user_data, expected_status=201, **kwargs):
        """
        Регистрация нового пользователя в системе (POST /register).
        Принимает структуру данных RegisterDto.
        """
        return self.send_request(
            method="POST",
            endpoint=REGISTER,
            data=user_data,
            expected_status=expected_status,
            **kwargs
        )

    def login_user(self, login_data, expected_status=201, **kwargs):
        """
        Аутентификация пользователя (POST /login).
        Принимает структуру данных LoginDto. По спецификации Cinescope успешный вход возвращает 201.
        """
        return self.send_request(
            method="POST",
            endpoint=LOGIN,
            data=login_data,
            expected_status=expected_status,
            **kwargs
        )

    def logout_user(self, expected_status=200, **kwargs):
        """
        Выход из учётной записи (GET /logout).
        Завершает текущую сессию пользователя на бэкенде.
        """
        return self.send_request(
            method="GET",
            endpoint=LOGOUT,
            expected_status=expected_status,
            **kwargs
        )

    def authenticate(self, user_creds: dict):
        """
        Выполняет полный цикл авторизации пользователя в рамках тестов.
        Получает токен доступа (accessToken) и автоматически сохраняет его
        в заголовках текущей HTTP-сессии для последующих защищенных запросов.
        """
        response = self.login_user(user_creds).json()

        if "accessToken" not in response:
            raise KeyError("token is missing in response")

        token = response["accessToken"]
        # Сохраняем Bearer токен в общие заголовки сессии requests
        self._update_session_headers({"Authorization": f"Bearer {token}"})