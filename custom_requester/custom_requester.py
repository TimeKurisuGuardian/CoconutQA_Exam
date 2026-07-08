import json
import logging
import os
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
        # Если в качестве данных ('data') в метод пришла Pydantic-модель, мы перехватываем её.
        if isinstance(data, BaseModel):
            # Переводим модель в JSON-строку (исключая незаполненные поля),
            # а затем обратно в чистый питонячий словарь (dict), который понимает библиотека requests.
            # Благодаря этому в самих тестах больше не нужно вручную писать .model_dump()!
            data = json.loads(data.model_dump_json(exclude_unset=True))

        # Отправляем реальный HTTP-запрос на сервер
        response = self.session.request(method, url, json=data, params=params, **kwargs)

        # Если логгирование включено, отправляем ответ в метод форматирования curl
        if need_logging:
            self.log_request_and_response(response)

        # Автоматическая проверка статус-кода ответа сервера
        if response.status_code != expected_status:
            # Если статус-код не совпал с ожидаемым (например, получили 400 вместо 201),
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
        Преобразует отправленный HTTP-запрос в готовый curl-командный формат для быстрого дебага в терминале.
        """
        try:
            request = response.request
            GREEN = '\033[32m'
            RED = '\033[31m'
            RESET = '\033[0m'

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

            # Записываем в лог красивый curl-запрос
            self.logger.info(f"\n{'=' * 40} REQUEST {'=' * 40}")
            self.logger.info(
                f"{GREEN}{full_test_name}{RESET}\n"
                f"curl -X {request.method} '{request.url}' \\\n"
                f"{headers} \\\n"
                f"{body}"
            )

            response_status = response.status_code
            is_success = response.ok
            response_data = response.text

            # Пытаемся сделать присланный сервером JSON красивым (добавляем отступы indent=4)
            try:
                response_data = json.dumps(json.loads(response.text), indent=4, ensure_ascii=False)
            except json.JSONDecodeError:
                pass  # Если сервер прислал не JSON, а обычный текст, оставляем как есть

            # Записываем в лог структурированный ответ от бэкенда
            self.logger.info(f"\n{'=' * 40} RESPONSE {'=' * 40}")
            if not is_success:
                # Если запрос неуспешный, то подсвечиваем статус и данные КРАСНЫМ цветом
                self.logger.info(
                    f"\tSTATUS_CODE: {RED}{response_status}{RESET}\n"
                    f"\tDATA: {RED}{response_data}{RESET}"
                )
            else:
                # Если всё ок, то подсвечиваем статус ЗЕЛЕНЫМ цветом
                self.logger.info(
                    f"\tSTATUS_CODE: {GREEN}{response_status}{RESET}\n"
                    f"\tDATA:\n{response_data}"
                )
            self.logger.info(f"{'=' * 80}\n")
        except Exception as e:
            self.logger.error(f"\nLogging failed: {type(e)} - {e}")