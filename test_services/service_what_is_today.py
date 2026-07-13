import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="Holiday Checker Service API",
    description="Локальный микросервис для определения государственных праздников РФ по переданной дате."
)


class DateTimeRequest(BaseModel):
    """Схема валидации входящего запроса с временной меткой."""
    currentDateTime: str  # Ожидаемый формат ISO: "2025-02-13T21:43Z"


# Словарь государственных праздников вынесен как глобальная константа (PEP-8 uppercase)
RUSSIAN_HOLIDAYS = {
    "01-01": "Новый год",
    "01-07": "Рождество Христово",
    "02-23": "День защитника Отечества",
    "03-08": "Международный женский день",
    "05-01": "Праздник Весны и Труда",
    "05-09": "День Победы",
    "06-12": "День России",
    "11-04": "День народного единства",
    "12-31": "Канун Нового года"
}


@app.post("/what_is_today", summary="Определить праздник по дате")
def what_is_today(request: DateTimeRequest):
    """
    Принимает временную метку в формате UTC ISO, парсит месяц и день,
    после чего сопоставляет их со словарём производственного календаря РФ.
    """
    try:
        # Парсинг строки даты в объект datetime
        date_obj = datetime.datetime.strptime(request.currentDateTime, "%Y-%m-%dT%H:%MZ")
        month_day = date_obj.strftime("%m-%d")

        # Поиск праздника в константе, дефолтное значение — будний день
        holiday = RUSSIAN_HOLIDAYS.get(month_day, "Сегодня нет праздников в России.")
        return {"message": holiday}

    except ValueError as e:
        # Валидация формата на уровне бизнес-логики с прокидыванием ошибки наружу
        raise HTTPException(
            status_code=400,
            detail=f"Некорректный формат даты. Ожидается '%Y-%m-%dT%H:%MZ'. Ошибка: {str(e)}"
        )


@app.get("/ping", summary="Проверка работоспособности сервиса (Health Check)")
def ping():
    """Возвращает стандартный ответ для проверки доступности эндпоинта мониторингом."""
    return "PONG!"


if __name__ == "__main__":
    # Запуск локального Uvicorn-сервера на выделенном порту 16002
    uvicorn.run(app, host="127.0.0.1", port=16002)