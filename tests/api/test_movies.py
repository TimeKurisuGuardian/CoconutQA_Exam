import random
import pytest
import allure
from pytest_check import check
from models.movie import MoviesListResponseModel
from db_models.movie import MovieDBModel

@pytest.fixture(scope="function")
def created_movie_via_api(api_manager, authenticated_admin):
    """Фикстура для подготовки тестовых данных (создание фильма) с последующим удалением."""
    movie_payload = {
        "name": f"API_Test_Movie_{random.randint(100, 999)}",
        "imageUrl": "https://image.url",
        "price": 350,
        "description": "Автоматически созданный фильм для проверки модификации данных",
        "location": "MSK",
        "published": True,
        "genreId": 10
    }

    with allure.step("Precondition: Создание фильма через POST /movies"):
        response = api_manager.movies.create_movie(movie_payload, expected_status=201)
        movie_data = response.json()
        yield movie_data

    with allure.step("Teardown: Удаление созданного фильма через DELETE /movies/{id}"):
        api_manager.movies.delete_movie(movie_data["id"], expected_status=[200, 204])


@allure.epic("Фильмы")
@allure.feature("Управление каталогом и афишей фильмов")
@pytest.mark.movies
class TestMoviesApi:

    @allure.story("Получение афиш фильмов")
    @allure.title("Позитивный сценарий: Параметризованная фильтрация фильмов по жанрам")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.label("owner", "pavel")
    @pytest.mark.parametrize("genre_id, expected_genre_name", [
        (4, "Криминал"),
        (10, "Военный"),
        (9, "Анимация"),
    ])
    def test_get_movies_by_genre_parametrization(self, api_manager, genre_id, expected_genre_name):
        params = {
            "page": 1,
            "pageSize": 5,
            "genreId": genre_id,
            "published": True
        }

        with allure.step(f"1. Отправка GET-запроса на /movies с кодом жанра {genre_id}"):
            response = api_manager.movies.get_movies(params=params, expected_status=200)
            json_response = response.json()

        with allure.step("2. Валидация схемы: Проверка JSON-ответа через Pydantic"):
            validated_data = MoviesListResponseModel(**json_response)

        with allure.step(f"3. Бизнес-проверка: Жанр фильмов в списке соответствует '{expected_genre_name}'"):
            if validated_data.count > 0:
                for movie in validated_data.movies:
                    assert movie.genre.name == expected_genre_name, \
                        f"Ожидали жанр {expected_genre_name}, но бэк вернул {movie.genre.name}"
            else:
                allure.attach("На стенде нет фильмов с этим жанром", name="Информация")

    @allure.story("Интеграция с базой данных")
    @allure.title("Интеграционный сценарий: Сверка данных афиши между API и Базой Данных")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.label("owner", "pavel")
    def test_verify_movie_integrity_with_db(self, api_manager, db_session):
        with allure.step("1. Получение актуального списка фильмов из API"):
            params = {"page": 1, "pageSize": 1, "published": True}
            response = api_manager.movies.get_movies(params=params, expected_status=200)
            validated_data = MoviesListResponseModel(**response.json())

            assert validated_data.count > 0, "Каталог фильмов пуст, нечего сверять с БД"
            api_movie = validated_data.movies[0]

        with allure.step(f"2. Прямой запрос к БД: Поиск фильма с ID={api_movie.id}"):
            db_movie = db_session.query(MovieDBModel).filter(MovieDBModel.id == api_movie.id).first()

        with allure.step("3. Валидация: Сверка полей (Soft Asserts)"):
            assert db_movie is not None, f"Фильм {api_movie.id} есть в API, но отсутствует в БД"

            with check:
                check.equal(db_movie.name, api_movie.name, "Название фильма в Базе Данных отличается от API")
                check.equal(db_movie.price, api_movie.price, "Цена билета в Базе Данных отличается от API")

            allure.attach(
                f"API: name='{api_movie.name}', price={api_movie.price}\n"
                f"DB:  name='{db_movie.name}', price={db_movie.price}",
                name="Сравнение API и DB",
                attachment_type=allure.attachment_type.TEXT
            )

    @allure.story("Модификация каталога фильмов")
    @allure.title("Позитивный сценарий: Создание нового фильма администратором")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.label("owner", "pavel")
    def test_create_movie_success(self, api_manager, authenticated_admin):
        unique_id = random.randint(1000, 9999)

        new_movie_payload = {
            "name": f"API_Test_Movie_{unique_id}",
            "imageUrl": "https://image.url",
            "price": 500,
            "description": "Позитивный сценарий создания фильма администратором",
            "location": "MSK",
            "published": True,
            "genreId": 10
        }

        with allure.step("1. Отправка POST-запроса на создание фильма"):
            response = api_manager.movies.create_movie(movie_data=new_movie_payload, expected_status=[200, 201])
            created_movie = response.json()

        with allure.step("2. Проверка полей созданного фильма в ответе бэкенда"):
            assert created_movie["name"] == new_movie_payload["name"], "Название фильма не совпало"
            assert created_movie["price"] == new_movie_payload["price"], "Цена фильма не совпала"
            assert "id" in created_movie, "Ответ бэкенда не содержит ID созданного фильма"

        with allure.step("3. POST-условие (Teardown): Удаление созданного фильма"):
            api_manager.movies.delete_movie(movie_id=created_movie["id"], expected_status=[200, 204])

    @allure.story("Модификация каталога фильмов")
    @allure.title("Позитивный сценарий: Изменение данных фильма (Редактирование)")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.label("owner", "pavel")
    def test_update_movie_data(self, api_manager, authenticated_admin, created_movie_via_api):
        movie = created_movie_via_api
        updated_payload = {
            "name": movie["name"] + " (Updated)",
            "price": movie["price"] + 100,
            "description": "Обновленное описание фильма в рамках тестирования API",
            "location": "SPB",
            "imageUrl": movie["imageUrl"],
            "published": True,
            "genreId": movie["genreId"]
        }

        with allure.step(f"1. Отправка PATCH-запроса на изменение фильма ID={movie['id']}"):
            response = api_manager.movies.update_movie(
                movie_id=movie["id"],
                movie_data=updated_payload,
                expected_status=[200, 201]  # Передаем список возможных успешных статусов для стабильности
            )
            response_json = response.json()

        with allure.step("2. Проверка модификации данных в ответе"):
            assert response_json["name"] == updated_payload["name"], "Название фильма не обновилось"
            assert response_json["price"] == updated_payload["price"], "Цена фильма не обновилась"

    @allure.story("Безопасность каталога фильмов")
    @allure.title("Негативный сценарий: Попытка создания фильма неавторизованным пользователем")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.label("owner", "pavel")
    def test_create_movie_unauthorized_forbidden(self, unauthenticated_api_manager):
        invalid_movie_payload = {
            "name": "Unauthorized Movie Object",
            "imageUrl": "https://image.url",
            "price": 0,
            "description": "Создание фильма должно быть отклонено протоколом безопасности",
            "location": "MSK",
            "published": True,
            "genreId": 1
        }

        with allure.step("1. Отправка POST-запроса на /movies без токена авторизации"):
            unauthenticated_api_manager.movies.create_movie(
                movie_data=invalid_movie_payload,
                expected_status=[401, 403]
            )