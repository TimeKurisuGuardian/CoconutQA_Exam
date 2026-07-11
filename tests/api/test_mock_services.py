import datetime
import requests
from pydantic import BaseModel
import sys  # Импортируем системный модуль, чтобы узнать точное имя текущего файла в памяти


class WorldClockResponse(BaseModel):
    currentDateTime: str


class WhatIsTodayResponse(BaseModel):
    message: str


def get_worldclockapi_time() -> WorldClockResponse:
    response = requests.get("http://worldclockapi.com/api/json/utc/now")
    assert response.status_code == 200, "Удаленный сервис недоступен"
    return WorldClockResponse(**response.json())


class TestTodayIsHolidayServiceAPI:

    # Тест 1: Проверяем обычный день
    def test_what_is_today(self, mocker):
        # sys.modules[__name__] — это железобетонный способ сказать: "патчи прямо в этом файле"
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

    # Тест 2: Проверяем Новый год
    def test_what_is_today_by_mocker(self, mocker):
        # Точно так же подменяем в текущем файле без всяких текстовых путей
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