import time
import random
import pytest
import allure
from pytest_check import check
from clients.api_manager import ApiManager
from models.user import RegisterUserResponseModel, UserCreationModel, UserRole


@allure.epic("Авторизация и профиль")
@allure.feature("Управление учетными записями пользователей")
class TestAuthApi:

    @allure.story("Базовая регистрация")
    @allure.title("Позитивный сценарий: Регистрация нового пользователя")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.label("owner", "pavel")
    def test_register_user(self, api_manager: ApiManager, test_user):
        """
        Позитивный тест на базовую регистрацию пользователя.
        Использует Pydantic-модель ответа для автоматической сквозной валидации
        всех полей, типов данных и формата даты бэкенда.
        """
        with allure.step("1. Отправка POST-запроса на регистрацию пользователя"):
            response = api_manager.auth_api.register_user(user_data=test_user)

        with allure.step("2. ДЕСЕРИАЛИЗАЦИЯ: Натягиваем сырой JSON-ответ на строгую модель ответа"):
            register_user_response = RegisterUserResponseModel(**response.json())

        with allure.step("3. Проверяем бизнес-логику: зарегистрировалась именно та почта, которую отправляли"):
            assert register_user_response.email == test_user.email, "Email в ответе API не совпадает с отправленным"


    @allure.story("Сквозные сценарии (End-to-End)")
    @allure.title("Интеграционный тест: Полный цикл жизни сессии (Регистрация -> Логин -> Доступ к API)")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.label("owner", "pavel")
    @pytest.mark.flaky(reruns=3, reruns_delay=2)  # Авто-перезапуск при моргании дев-стенда
    def test_full_auth_and_profile_flow(self, api_manager, faker):
        """
        Интеграционный тест полного цикла (End-to-End).
        Эмулирует реальный путь пользователя: Регистрация -> Логин (Аутентификация) ->
        Проверка доступа к защищенному эндпоинту (Фильмы) по сгенерированному токену.
        """
        with allure.step("1. Генерация уникальных случайных данных"):
            # Используем чистые цифры для обхода строгого валидатора имейлов на бэкенде
            random_id = random.randint(100000, 999999)
            username = f"user{random_id}"
            password = "ValidPassword123"
            email = f"pavelqa{random_id}{int(time.time()) % 10000}@gmail.com"
            name = faker.name()

            # Обернули в модель для унификации структуры запросов
            user_model = UserCreationModel(
                email=email,
                fullName=name,
                password=password,
                passwordRepeat=password,
                roles=[UserRole.USER]
            )

        with allure.step("2. Выполнение запроса на регистрацию аккаунта (Ожидаемый статус: 200 или 201)"):
            # Наш кастомный реквестер теперь поддерживает списки статусов для гибкости стенда
            api_manager.auth_api.register_user(user_model, expected_status=[200, 201])

        with allure.step("3. Аутентификация пользователя и сохранение токена в сессию"):
            login_payload = {
                "email": email,
                "password": password
            }
            api_manager.auth_api.authenticate(login_payload)

        with allure.step("4. Запрос к защищенному эндпоинту фильмов (Ожидаемый статус: 200)"):
            movies_response = api_manager.movies.get_movies(expected_status=200)
            response_json = movies_response.json()

        with allure.step("5. Комплексная проверка структуры ответа (Мягкие проверки Soft Asserts)"):
            # Мягкие проверки позволяют проверить всю структуру, даже если один из ассертов упадет
            with check:
                check.is_in("movies", response_json, "Ключ 'movies' отсутствует в ответе сервера")
                if "movies" in response_json:
                    check.is_instance(response_json["movies"], list, "Поле 'movies' должно быть списком")


    @allure.story("Безопасность и валидация")
    @allure.title("Негативный сценарий: Попытка входа с некорректными учетными данными")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.label("owner", "pavel")
    def test_login_with_invalid_credentials(self, api_manager, faker):
        """
        Негативный тест на аутентификацию.
        Проверяет, что система безопасности бэкенда корректно отрабатывает
        и возвращает ошибку 401 Unauthorized при попытке входа с фейковыми данными.
        """
        with allure.step("1. Генерация случайных невалидных данных"):
            invalid_payload = {
                "email": f"fake{random.randint(100, 999)}@invalid.com",
                "password": faker.password()
            }

        with allure.step("2. Отправка запроса и проверка строгой ошибки 401 Unauthorized"):
            api_manager.auth_api.login_user(invalid_payload, expected_status=401)