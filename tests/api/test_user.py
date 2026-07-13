import pytest
from models.user import RegisterUserResponseModel


class TestUser:

    def test_create_user(self, api_manager, super_admin, creation_user_data):
        """
        Позитивный тест: Создание нового пользователя через права Супер-Админа.
        Проверяет, что администратор может успешно создавать объекты в базе,
        а бэкенд возвращает корректную заполненную структуру.
        """
        # 1. ОТПРАВКА: Передаем модель creation_user_data напрямую.
        #    Наш прокачанный CustomRequester сам переведет её в JSON.
        #    Ответ сервера (.json()) получаем сразу в виде словаря.
        response = api_manager.user_api.create_user(creation_user_data).json()

        # 2. ВАЛИДАЦИЯ СХЕМЫ: Натягиваем пришедший ответ на модель Pydantic.
        #    Она автоматически проверит наличие полей, типы данных (str, bool) и формат даты.
        validated_response = RegisterUserResponseModel(**response)

        # 3. БИЗНЕС-ПРОВЕРКА: Сверяем, что сервер создал именно то, что мы просили
        assert validated_response.email == creation_user_data.email, "Email на бэкенде не совпадает с отправленным"
        assert validated_response.fullName == creation_user_data.fullName, "Имя на бэкенде не совпадает с отправленным"
        assert validated_response.verified is True, "Флаг верификации (verified) должен быть True"
        assert validated_response.id != "", "Бэкенд вернул пустой ID пользователя"

    def test_get_user_by_locator(self, api_manager, super_admin, creation_user_data):
        """
        Позитивный тест: Проверка поиска (локатора) пользователя.
        Убеждается, что созданного пользователя можно одинаково успешно найти
        как по его уникальному ID, так и по его Email адресу.
        """
        # 1. Создаем пользователя на бэкенде (снова без .model_dump(), реквестер сделает сам)
        created_user_response = api_manager.user_api.create_user(creation_user_data).json()

        # 2. Переводим ответ в Pydantic, чтобы безопасно вытащить сгенерированный сервером ID
        user_info = RegisterUserResponseModel(**created_user_response)

        # 3. Запрашиваем информацию о пользователе двумя РАЗНЫМИ путями:
        #    Сначала стучимся по ID, а затем по Email
        response_by_id = api_manager.user_api.get_user_info(user_info.id).json()
        response_by_email = api_manager.user_api.get_user_info(creation_user_data.email).json()

        # 4. Сравниваем два ответа: бэкенд обязан вернуть абсолютно идентичные JSON-данные
        assert response_by_id == response_by_email, "Содержание ответов по ID и по Email должно быть идентичным"

        # 5. Дополнительно валидируем структуру ответа поиска через Pydantic-модель
        validated_response = RegisterUserResponseModel(**response_by_id)
        assert validated_response.id == user_info.id, "ID найденного пользователя не совпадает с исходным"

    def test_get_user_by_id_common_user_forbidden(self, api_manager, common_user):
        """
        Негативный тест: Ролевая модель и безопасность.
        Проверяет, что у обычного пользователя (роль USER) нет прав запрашивать
        информацию о чужих аккаунтах. Бэкенд должен жестко возвращать статус 403 Forbidden.
        """
        # Отправляем запрос от лица обычного юзера (common_user).
        # Параметр expected_status=403 говорит реквестеру: мы ЖДЕМ ошибку 403.
        # Если бэкенд отдаст данные (вернет 200), реквестер сам уронит этот тест.
        api_manager.user_api.get_user_info(common_user.email, expected_status=403)

    def test_check_me_endpoint_directly(self, api_manager, authenticated_user):
        """Быстрый сисадминский тест для проверки эндпоинта /user/me"""

        # Запрос делаем через api_manager!
        response = api_manager.user_api.get_user_info(user_id="me")

        assert response.status_code == 200, f"Ошибка! Бэк вернул код: {response.status_code}"
        print(f"\n[УСПЕХ]: Эндпоинт /user/me работает! Текущий юзер в базе: {response.json().get('email')}")