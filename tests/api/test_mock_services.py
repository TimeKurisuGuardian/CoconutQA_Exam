import datetime
import sys
import pytz
import requests
from pydantic import BaseModel


# =====================================================================
# Pydantic-модели для валидации запросов и ответов API
# =====================================================================

class DateTimeRequest(BaseModel):
    """Модель входящего запроса для передачи даты на сервер праздников."""
    currentDateTime: str


class WorldClockResponse(BaseModel):
    """Модель ответа от внешнего (или фейкового) сервиса мирового времени."""
    currentDateTime: str


class WhatIsTodayResponse(BaseModel):
    """Модель ответа от целевого сервиса проверки праздников."""
    message: str


# =====================================================================
# Клиентские методы (Функции выполнения HTTP-запросов)
# =====================================================================

def get_worldclockapi_time() -> WorldClockResponse:
    """Выполняет реальный запрос во внешний сервис времени."""
    response = requests.get("http://worldclockapi.com/api/json/utc/now")
    assert response.status_code == 200, "Удаленный сервис времени недоступен"
    return WorldClockResponse(**response.json())


def get_fake_worldclockapi_time() -> WorldClockResponse:
    """
    Выполняет запрос в наш локальный Fake-сервер времени.
    Исправлено: урл указывает на локальный симулятор (порт 16001).
    """
    response = requests.get("http://127.0.0.1:16001/fake/worldclockapi/api/json/utc/now")
    assert response.status_code == 200, "Локальный Fake-сервер времени недоступен"
    return WorldClockResponse(**response.json())


# =====================================================================
# Тестовый класс с демонстрацией различных техник изолированного тестирования
# =====================================================================

class TestTodayIsHolidayServiceAPI:

    def run_wiremock_worldclockapi_time(self):
        """
        Вспомогательный метод (Helper) для конфигурации маппинга в WireMock.
        Отправляет JSON-схему ожидания во внешний mock-сервер.
        """
        wiremock_url = "http://localhost:8080/__admin/mappings"
        mapping = {
            "request": {
                "method": "GET",
                "url": "/wire/mock/api/json/utc/now"
            },
            "response": {
                "status": 200,
                "body": '''{
                        "$id": "1",
                        "currentDateTime": "2025-03-08T00:00Z",
                        "utcOffset": "00:00",
                        "isDayLightSavingsTime": false,
                        "dayOfTheWeek": "Wednesday",
                        "timeZoneName": "UTC",
                        "currentFileTime": 1324567890123,
                        "ordinalDate": "2025-1",
                        "serviceResponse": null
                    }'''
            }
        }
        response = requests.post(wiremock_url, json=mapping)
        assert response.status_code == 201, "Не удалось настроить маппинг в WireMock"

    def test_what_is_today(self, mocker):
        """Тест 1: Использование unittest.mock через фикстуру mocker (Обычный день)."""
        # Динамическое определение контекста модуля через sys.modules для стабильного патчинга
        mocker.patch.object(
            sys.modules[__name__],
            "get_worldclockapi_time",
            return_value=WorldClockResponse(currentDateTime="2025-02-13T21:43Z")
        )

        world_clock_response = get_worldclockapi_time()
        payload = {"currentDateTime": world_clock_response.currentDateTime}
        what_is_today_response = requests.post("http://127.0.0.1:16002/what_is_today", json=payload)

        assert what_is_today_response.status_code == 200
        data = WhatIsTodayResponse(**what_is_today_response.json())
        assert data.message == "Сегодня нет праздников в России."

    def test_what_is_today_by_mocker(self, mocker):
        """Тест 2: Использование mocker для подмены даты на праздничный день (Новый год)."""
        mocker.patch.object(
            sys.modules[__name__],
            "get_worldclockapi_time",
            return_value=WorldClockResponse(currentDateTime="2025-01-01T12:00Z")
        )

        world_clock_response = get_worldclockapi_time()
        payload = {"currentDateTime": world_clock_response.currentDateTime}
        what_is_today_response = requests.post("http://127.0.0.1:16002/what_is_today", json=payload)

        assert what_is_today_response.status_code == 200
        data = WhatIsTodayResponse(**what_is_today_response.json())
        assert data.message == "Новый год"

    def test_what_is_today_by_stub(self, monkeypatch):
        """Тест 3: Использование классического Stub (Заглушки) через встроенный monkeypatch (День Победы)."""

        def fake_get_time():
            return WorldClockResponse(currentDateTime="2025-05-09T12:00Z")

        # Переопределяем оригинальную функцию локальным стабом
        monkeypatch.setattr(
            sys.modules[__name__],
            "get_worldclockapi_time",
            fake_get_time
        )

        world_clock_response = get_worldclockapi_time()
        payload = {"currentDateTime": world_clock_response.currentDateTime}
        what_is_today_response = requests.post("http://127.0.0.1:16002/what_is_today", json=payload)

        assert what_is_today_response.status_code == 200
        data = WhatIsTodayResponse(**what_is_today_response.json())
        assert data.message == "День Победы"

    def test_what_is_today_by_wiremock(self):
        """Тест 4: Интеграция со сторонним инструментом WireMock (Docker) для симуляции внешнего API (8 марта)."""
        # 1. Загружаем конфигурацию в контейнер WireMock
        self.run_wiremock_worldclockapi_time()

        # 2. Выполняем GET-запрос к эмулируемому сетевому эндпоинту
        world_clock_response = requests.get("http://localhost:8080/wire/mock/api/json/utc/now")
        assert world_clock_response.status_code == 200
        current_date_time = WorldClockResponse(**world_clock_response.json()).currentDateTime

        # 3. Передаем полученную дату на наш локальный сервис праздников (FastAPI)
        # Использование аргумента json обеспечивает автоматическую установку Content-Type: application/json
        payload = DateTimeRequest(currentDateTime=current_date_time).model_dump()
        what_is_today_response = requests.post(
            "http://127.0.0.1:16002/what_is_today",
            json=payload
        )

        assert what_is_today_response.status_code == 200
        what_is_today_data = WhatIsTodayResponse(**what_is_today_response.json())
        assert what_is_today_data.message == "Международный женский день"

    def test_fake_worldclockapi(self):
        """Тест 5: Верификация работоспособности собственного кастомного Fake-сервиса времени."""
        world_clock_response = get_fake_worldclockapi_time()
        current_date_time = world_clock_response.currentDateTime
        print(f"\nТекущая дата и время из фейка: {current_date_time=}")

        # Сравниваем возвращенное сервером время с текущим актуальным временем в UTC
        expected_time = datetime.datetime.now(pytz.utc).strftime("%Y-%m-%dT%H:%MZ")
        assert current_date_time == expected_time, "Возвращаемая фейком дата не валидна"

    def test_fake_what_is_today(self):
        """Тест 6: Комплексная проверка интеграции целевого сервиса праздников с кастомным Fake-сервисом."""
        # 1. Запрашиваем динамические данные времени у Fake-сервера
        world_clock_response = get_fake_worldclockapi_time()

        # 2. Перенаправляем данные в целевой сервис праздников для верификации бизнес-логики
        payload = DateTimeRequest(currentDateTime=world_clock_response.currentDateTime).model_dump()
        what_is_today_response = requests.post("http://127.0.0.1:16002/what_is_today", json=payload)

        assert what_is_today_response.status_code == 200
        result_data = WhatIsTodayResponse(**what_is_today_response.json())

        # Для текущей динамической даты праздники в словаре отсутствуют, ожидаем стандартный ответ
        assert result_data.message == "Сегодня нет праздников в России."