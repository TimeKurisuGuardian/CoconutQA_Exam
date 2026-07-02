import time


def test_full_auth_and_profile_flow(api_manager, faker):
    """
    Интеграционный тест для проверки полной цепочки авторизации.
    Регистрирует нового пользователя, выполняет аутентификацию
    и проверяет доступ к защищенным ресурсам (списку фильмов).
    """
    username = faker.user_name()
    password = "ValidPassword123"
    email = f"user_{int(time.time())}@example.com"
    name = faker.name()

    user_payload = {
        "email": email,
        "username": username,
        "password": password,
        "passwordRepeat": password,
        "fullName": name
    }

    # Регистрация нового аккаунта в системе
    api_manager.auth_api.register_user(user_payload, expected_status=201)

    # Аутентификация и автоматическое сохранение токена в сессии
    login_payload = {
        "email": email,
        "password": password
    }
    api_manager.auth_api.authenticate(login_payload)

    # Проверка работоспособности токена через запрос защищенного эндпоинта
    movies_response = api_manager.movies.get_movies(expected_status=200)

    assert "movies" in movies_response.json(), "Ключ 'movies' отсутствует в ответе сервера"


def test_login_with_invalid_credentials(api_manager, faker):
    """
    Негативный тест на аутентификацию.
    Проверяет, что система возвращает ошибку 401 Unauthorized
    при попытке входа с невалидными учетными данными.
    """
    invalid_payload = {
        "username": faker.user_name(),
        "password": faker.password()
    }
    api_manager.auth_api.login_user(invalid_payload, expected_status=401)