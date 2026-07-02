import json
import logging
import os


class CustomRequester:
    """
    Базовый класс для отправки HTTP-запросов.
    Обеспечивает автоматическую валидацию статус-кодов,
    логирование запросов/ответов в формате curl и управление заголовками сессии.
    """
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
        Выполняет логирование и проверку соответствия фактического статус-кода ожидаемому.
        """
        url = f"{self.base_url}{endpoint}"

        # Передача параметров в requests с автоматической конвертацией данных в JSON
        response = self.session.request(method, url, json=data, params=params, **kwargs)

        if need_logging:
            self.log_request_and_response(response)

        if response.status_code != expected_status:
            # Принудительный вывод тела ошибки в консоль при несовпадении статус-кода
            print("\n" + "=" * 20 + " БЭКЕНД ВЕРНУЛ ОШИБКУ " + "=" * 20)
            print(response.text)
            print("=" * 62 + "\n")

            raise ValueError(
                f"Unexpected status code: {response.status_code}. Expected: {expected_status}"
            )
        return response

    def _update_session_headers(self, headers: dict):
        """Обновление заголовков текущей HTTP-сессии (например, добавление Bearer токена)."""
        self.session.headers.update(headers)

    def log_request_and_response(self, response):
        """
        Форматированное логирование отправленного запроса и полученного ответа.
        Запрос преобразуется в готовый curl-командный формат для удобного дебага.
        """
        try:
            request = response.request
            GREEN = '\033[32m'
            RED = '\033[31m'
            RESET = '\033[0m'

            full_test_name = f"pytest {os.environ.get('PYTEST_CURRENT_TEST', '').replace(' (call)', '')}"
            headers = " \\\n".join([f"-H '{header}: {value}'" for header, value in request.headers.items()])

            body = ""
            if hasattr(request, 'body') and request.body is not None:
                if isinstance(request.body, bytes):
                    body = request.body.decode('utf-8')
                elif isinstance(request.body, str):
                    body = request.body
                body = f"-d '{body}' \n" if body and body != '{}' else ''

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

            try:
                response_data = json.dumps(json.loads(response.text), indent=4, ensure_ascii=False)
            except json.JSONDecodeError:
                pass

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
        except Exception as e:
            self.logger.error(f"\nLogging failed: {type(e)} - {e}")