import pytest

def test_check_network_soon_in_db(db_helper):
    """Тест проверяет наличие фильма 'Network soon.' в БД и валидирует его параметры"""

    # 1. Задаем имя фильма для поиска (данные проверены через DBeaver)
    target_movie_name = "Network soon."

    # 2. Вызываем метод поиска через db_helper
    # Хелпер выполняет SELECT-запрос через сессию SQLAlchemy и возвращает объект модели
    movie = db_helper.get_movie_by_name(target_movie_name)

    # 3. Проверка (Validation)
    assert movie is not None, f"Фильм '{target_movie_name}' не найден в базе данных!"
    print(f"\n[База данных]: Успешно нашли фильм: {movie}")

    # Проверяем корректность стоимости
    assert movie.price == 130, f"Ожидали цену 130, но в базе зафиксировано: {movie.price}"

    # Проверяем статус публикации
    assert movie.published is True, "Фильм имеет статус 'не опубликован'!"