import json
import logging
import os
import allure
from pydantic import BaseModel

# Задаем ANSI-коды цветов напрямую, чтобы логи в консоли были цветными
GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"


class CustomRequester:
    """
    Базовый класс для отправки HTTP-запросов.
    Обеспечивает автоматическую валидацию статус-кодов,
    логирование запросов/ответов в формате curl и управление заголовками сессии.
    """

    # Стандартные заголовки, которые нужны для работы с JSON API
    base_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    def __init__(self, session, base_url):
        self.session = session
        self.base_url = base_url
        self.headers = self.base_headers.copy()
        self.session.headers.update(self.base_headers)
        self.logger = logging.getLogger(__name__)

    def send_request(self, method, endpoint, data=None, params=None, expected_status=200, need_logging=True, **kwargs):
        """
        Универсальный метод для отправки HTTP-запросов через текущую сессию.
        Выполняет автоматическую сериализацию Pydantic-моделей, логирование и проверку статус-кодов.
        """
        # Собираем полный URL (например: http://api.site.com + /user)
        url = f"{self.base_url}{endpoint}"

        # АВТОМАТИЧЕСКАЯ ВАЛИДАЦИЯ И СЕРИАЛИЗАЦИЯ ДАННЫХ:
        if isinstance(data, BaseModel):
            data = json.loads(data.model_dump_json(exclude_unset=True))

        # Отправляем реальный HTTP-запрос на сервер
        response = self.session.request(method, url, json=data, params=params, **kwargs)

        # Если логирование включено, отправляем ответ в метод форматирования
        if need_logging:
            self.log_request_and_response(response)

        # Автоматическая проверка статус-кода ответа сервера
        if isinstance(expected_status, (list, tuple)):
            is_status_error = response.status_code not in expected_status
        else:
            is_status_error = response.status_code != expected_status

        if is_status_error:
            # Если статус-код не совпал с ожидаемым,
            # принудительно выводим сырой текст ошибки от бэкенда в консоль для дебага
            print("\n" + "=" * 20 + " БЭКЕНД ВЕРНУЛ ОШИБКУ " + "=" * 20)
            print(response.text)
            print("=" * 62 + "\n")

            # Роняем тест с понятным описанием проблемы
            raise ValueError(
                f"Unexpected status code: {response.status_code}. Expected: {expected_status}"
            )

        return response

    def _update_session_headers(self, headers: dict):
        """Обновление заголовков текущей HTTP-сессии (например, добавление Bearer токена авторизации)."""
        self.session.headers.update(headers)

    def log_request_and_response(self, response):
        """
        Форматированное логирование отправленного запроса и полученного ответа.
        Преобразует отправленный HTTP-запрос в готовый curl-командный формат для быстрого дебага,
        а также автоматически прикрепляет логи к Allure-отчёту.
        """
        try:
            request = response.request

            # Вытаскиваем имя текущего запущенного теста из окружения Pytest
            full_test_name = f"pytest {os.environ.get('PYTEST_CURRENT_TEST', '').replace(' (call)', '')}"

            # Собираем заголовки запроса в curl-формат через знак переноса строки \
            headers = " \\\n".join([f"-H '{header}: {value}'" for header, value in request.headers.items()])

            # Форматируем тело запроса (body), если оно присутствует
            body = ""
            if hasattr(request, 'body') and request.body is not None:
                if isinstance(request.body, bytes):
                    body = request.body.decode('utf-8')
                elif isinstance(request.body, str):
                    body = request.body
                body = f"-d '{body}' \n" if body and body != '{}' else ''

            # Формируем красивую строку curl для логов и Allure
            curl_command = (
                f"curl -X {request.method} '{request.url}' \\\n"
                f"{headers} \\\n"
                f"{body}"
            )

            # Записываем в лог консоли красивый curl-запрос
            self.logger.info(f"\n{'=' * 40} REQUEST {'=' * 40}")
            self.logger.info(f"{GREEN}{full_test_name}{RESET}\n{curl_command}")

            response_status = response.status_code
            is_success = response.ok
            response_data = response.text

            # Пытаемся сделать присланный сервером JSON красивым (добавляем отступы indent=4)
            try:
                response_data = json.dumps(json.loads(response.text), indent=4, ensure_ascii=False)
            except json.JSONDecodeError:
                pass

            # Записываем в лог консоли структурированный ответ от бэкенда
            self.logger.info(f"\n{'=' * 40} RESPONSE {'=' * 40}")
            if not is_success:
                self.logger.info(
                    f"\tSTATUS_CODE: {RED}{response_status}{RESET}\n"
                    f"\tDATA: {RED}{response_data}{RESET}"
                )
            else:
                self.logger.info(
                    f"\tSTATUS_CODE: {GREEN}{response_status}{RESET}\n"
                    f"\tDATA:\n{response_data}"
                )
            self.logger.info(f"{'=' * 80}\n")

            # --- ИНТЕГРАЦИЯ С ALLURE ---
            # Прикрепляем curl-запрос к текущему шагу теста в Allure
            allure.attach(
                curl_command,
                name=f"API Request: {request.method} {request.url.split('/')[-1]}",
                attachment_type=allure.attachment_type.TEXT
            )
            # Прикрепляем JSON-ответ бэкенда к текущему шагу теста в Allure
            allure.attach(
                f"STATUS CODE: {response_status}\n\nDATA:\n{response_data}",
                name=f"API Response: {response_status}",
                attachment_type=allure.attachment_type.TEXT
            )

        except Exception as e:
            self.logger.error(f"\nLogging failed: {type(e)} - {e}")