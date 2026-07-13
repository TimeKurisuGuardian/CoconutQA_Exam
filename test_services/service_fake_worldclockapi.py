from datetime import datetime
from fastapi import FastAPI
import pytz

app = FastAPI(
    title="Fake WorldClock API Simulator",
    description="Симулятор внешнего сервиса времени worldclockapi.com для изолированного интеграционного тестирования."
)


@app.get("/ping", summary="Health Check")
def ping():
    """Проверка доступности фейкового сервиса."""
    return "PONG!"


@app.get("/fake/worldclockapi/api/json/utc/now", summary="Имитация получения UTC времени")
def get_current_utc_time():
    """
    Генерирует и возвращает динамический JSON-пакет, полностью 
    дублирующий структуру ответов реального сервиса worldclockapi.com.
    Позволяет симулировать любые временные метки без обращения к внешней сети.
    """
    # Расчет текущего актуального времени в таймзоне UTC
    now = datetime.now(pytz.utc)

    # Формирование сигнатуры ответа оригинального API
    response = {
        "$id": "1",
        "currentDateTime": now.strftime("%Y-%m-%dT%H:%MZ"),
        "utcOffset": "00:00:00",
        "isDayLightSavingsTime": False,
        "dayOfTheWeek": now.strftime("%A"),
        "timeZoneName": "UTC",
        # Конвертация в FILETIME (100-наносекундные интервалы, отсчитываемые с 1 января 1601 года)
        "currentFileTime": int(now.timestamp() * 10 ** 7),
        # Формат ordinalDate: Год-Порядковый день в году (001-366)
        "ordinalDate": now.strftime("%Y-%j"),
        "serviceResponse": None
    }

    return response


if __name__ == "__main__":
    import uvicorn

    # Запуск симулятора на порту 16001
    uvicorn.run(app, host="0.0.0.0", port=16001)

# =====================================================================
# ИНСТРУКЦИЯ ПО ДИАГНОСТИКЕ И ЗАПУСКУ СЕРВИСА:
# 
# 1. Установка зависимостей:
#    pip install -r requirements.txt
# 
# 2. Запуск локального сервера:
#    python test_services\service_fake_worldclockapi.py
# 
# 3. Верификация эндпоинтов через cURL:
#    curl http://127.0.0.1:16001/ping
#    curl http://127.0.0.1:16001/fake/worldclockapi/api/json/utc/now
# =====================================================================