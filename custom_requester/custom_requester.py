import json
import logging
import os
from typing import Union, List, Tuple, Dict, Any
import allure
import requests
from pydantic import BaseModel

GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"


class CustomRequester:
    """
    Базовый класс для отправки HTTP-запросов.
    Обеспечивает автоматическую валидацию статус-кодов,
    логирование запросов/ответов в формате curl и управление заголовками сессии.
    """

    base_headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    def __init__(self, session: requests.Session, base_url: str):
        self.session = session
        self.base_url = base_url
        self.headers = self.base_headers.copy()
        self.session.headers.update(self.base_headers)
        self.logger = logging.getLogger(__name__)

    def send_request(
        self,
        method: str,
        endpoint: str,
        data: Any = None,
        params: Any = None,
        expected_status: Union[int, List[int], Tuple[int], None] = 200,
        need_logging: bool = True,
        **kwargs
    ) -> requests.Response:
        """
        Универсальный метод для отправки HTTP-запросов через текущую сессию.
        Выполняет автоматическую сериализацию Pydantic-моделей, логирование и проверку статус-кодов.
        """
        url = f"{self.base_url}{endpoint}"

        if isinstance(data, BaseModel):
            data = json.loads(data.model_dump_json(exclude_unset=True))

        response = self.session.request(method, url, json=data, params=params, **kwargs)

        if need_logging:
            self.log_request_and_response(response)

        if expected_status is not None:
            if isinstance(expected_status, (list, tuple)):
                is_status_error = response.status_code not in expected_status
                expected_str = f"one of {expected_status}"
            else:
                is_status_error = response.status_code != expected_status
                expected_str = str(expected_status)

            if is_status_error:
                print("\n" + "=" * 20 + " БЭКЕНД ВЕРНУЛ ОШИБКУ " + "=" * 20)
                print(response.text)
                print("=" * 62 + "\n")

                raise ValueError(
                    f"Unexpected status code: {response.status_code}. Expected: {expected_str}"
                )

        return response

    def _update_session_headers(self, headers: dict):
        """Обновление заголовков текущей HTTP-сессии."""
        self.session.headers.update(headers)

    def log_request_and_response(self, response: requests.Response):
        """
        Форматированное логирование отправленного запроса и полученного ответа.
        Преобразует отправленный HTTP-запрос в готовый curl-формат и прикрепляет логи к Allure-отчёту.
        """
        try:
            request = response.request
            full_test_name = f"pytest {os.environ.get('PYTEST_CURRENT_TEST', '').replace(' (call)', '')}"
            headers = " \\\n".join([f"-H '{header}: {value}'" for header, value in request.headers.items()])

            body = ""
            if hasattr(request, 'body') and request.body is not None:
                if isinstance(request.body, bytes):
                    body = request.body.decode('utf-8')
                elif isinstance(request.body, str):
                    body = request.body
                body = f"-d '{body}' \n" if body and body != '{}' else ''

            curl_command = (
                f"curl -X {request.method} '{request.url}' \\\n"
                f"{headers} \\\n"
                f"{body}"
            )

            self.logger.info(f"\n{'=' * 40} REQUEST {'=' * 40}")
            self.logger.info(f"{GREEN}{full_test_name}{RESET}\n{curl_command}")

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

            allure.attach(
                curl_command,
                name=f"API Request: {request.method} {request.url.split('/')[-1]}",
                attachment_type=allure.attachment_type.TEXT
            )
            allure.attach(
                f"STATUS CODE: {response_status}\n\nDATA:\n{response_data}",
                name=f"API Response: {response_status}",
                attachment_type=allure.attachment_type.TEXT
            )

        except Exception as e:
            self.logger.error(f"\nLogging failed: {type(e)} - {e}")