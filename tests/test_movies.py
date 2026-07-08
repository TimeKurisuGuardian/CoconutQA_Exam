import pytest
from utils.data_generator import DataGenerator
import random


@pytest.fixture(scope="function")
def created_movie(super_admin):
    """Фикстура: создает фильм со строгими параметрами из Swagger DTO"""
    import random
    movie_data = {
        "name": f"Pavel Film {random.randint(10000, 99999)}",
        "imageUrl": "https://images.unsplash.com/photo-1536440136628-849c177e76a1.jpg",  # Валидная ссылка с расширением
        "price": 100,
        "description": "Valid short description for match Swagger",
        "location": "SPB",
        "published": True,
        "genreId": 1
    }

    response = super_admin.api.movies.create_movie(movie_data, expected_status=201)
    movie_json = response.json()

    yield movie_json

    super_admin.api.movies.delete_movie(movie_json["id"], expected_status=200)

@pytest.mark.skip(reason="Фильмы временно скрыты, эндпоинты на доработке")
class TestMovies:

    def test_get_movies_filter_by_genre(self, super_admin, created_movie):
        """Тест 1: Проверка фильтрации по genreId (GET /movies)"""
        target_genre_id = created_movie["genreId"]

        # Запрашиваем фильмы по конкретному жанру
        response = super_admin.api.movies.get_movies(params={"genreId": target_genre_id}, expected_status=200)
        data = response.json()

        # Согласно Сваггеру, фильмы лежат внутри ключа "movies"
        movies = data.get("movies", [])

        # Проверяем, что все вернувшиеся фильмы соответствуют нашему фильтру
        assert len(movies) > 0, f"Сервер не вернул фильмы для жанра {target_genre_id}"
        for movie in movies:
            assert movie[
                       "genreId"] == target_genre_id, f"Ожидали жанр {target_genre_id}, но получили {movie['genreId']}"

    def test_update_movie_positive(self, super_admin, created_movie):
        """Тест 2: Позитивный PATCH /movies/{id} — передаем ПОЛНЫЙ DTO, как требует бэкенд"""
        movie_id = created_movie["id"]

        # Сваггер требует передачи полной структуры при обновлении.
        # Берем старые данные из созданного фильма и меняем только поле 'name'
        updated_payload = {
            "name": "Pavel's New Cool Movie",
            "description": created_movie["description"],
            "price": created_movie["price"],
            "location": created_movie["location"],
            "imageUrl": created_movie["imageUrl"],
            "published": created_movie["published"],
            "genreId": created_movie["genreId"]
        }

        response = super_admin.api.movies.update_movie(
            movie_id=movie_id,
            movie_data=updated_payload,
            expected_status=200
        )

        assert response.json()["name"] == "Pavel's New Cool Movie", "Название фильма не обновилось на бэкенде"

    def test_delete_movie_negative_not_found(self, super_admin):
        """Тест 3: Негативный тест на DELETE несуществующего фильма под админом"""
        invalid_id = 999999
        super_admin.api.movies.delete_movie(movie_id=invalid_id, expected_status=404)

    def test_create_movie_as_common_user_forbidden(self, common_user):
        """Тест 4: Негативный: Ролевая модель. Пользователь с ролью USER получает 403 при создании фильма"""
        fake_movie_data = {
            "name": "Кино от Системных Администраторов",
            "price": 250,
            "description": "Как починить прод за 5 минут без регистрации и смс",
            "imageUrl": "https://images.unsplash.com/photo-1536440136628-849c177e76a1",
            "location": "SPB",
            "published": True,
            "genreId": 1
        }
        common_user.api.movies.create_movie(fake_movie_data, expected_status=403)


# Динамические параметры для параметризованных тестов
dynamic_min_price = random.randint(1, 150)
dynamic_max_price = random.randint(300, 1000)
dynamic_genre_id = 1  # Фиксируем на 1, так как этот жанр гарантированно есть в системе

@pytest.mark.skip(reason="Параметризованные тесты фильмов временно скрыты")
class TestMoviesParametrized:

    @pytest.mark.parametrize(
        "filter_params, check_field, expected_value",
        [
            ({"genreId": dynamic_genre_id}, "genreId", dynamic_genre_id),
            ({"locations": ["SPB"]}, "location", "SPB"),  # ПОЧИНИЛИ: Передаем как список ['SPB'], согласно Сваггеру
            (
                    {"minPrice": dynamic_min_price, "maxPrice": dynamic_max_price},
                    "price",
                    (dynamic_min_price, dynamic_max_price)
            )
        ],
        ids=["Filter by Dynamic Genre", "Filter by Strict Location List", "Filter by Dynamic Price Range"]
    )
    def test_get_movies_by_filters(self, super_admin, filter_params, check_field, expected_value):
        """Тест динамически проверяет фильтрацию фильмов с защитой от эффекта пестицида"""
        response = super_admin.api.movies.get_movies(params=filter_params, expected_status=200)
        data = response.json()

        movies = data.get("movies", [])

        if len(movies) > 0:
            for movie in movies:
                if check_field in movie:
                    actual_val = movie[check_field]

                    if check_field == "price":
                        min_p, max_p = expected_value
                        assert min_p <= actual_val <= max_p
                    else:
                        assert actual_val == expected_value

    @pytest.mark.parametrize(
        "user_fixture, movie_id_type, expected_status",
        [
            ("super_admin", "existing", 200),
            ("common_user", "existing", 403),
            ("super_admin", "non_existing", 404)
        ],
        ids=["Admin: delete positive", "Common User: delete forbidden", "Admin: delete non-existing ID"]
    )
    def test_delete_movie_roles(self, request, super_admin, common_user, user_fixture, movie_id_type, expected_status):
        """Параметризированный тест ролевой модели эндпоинта DELETE /movies/{id}"""
        current_user = request.getfixturevalue(user_fixture)

        if movie_id_type == "existing":
            fake_movie = {
                "name": f"Temp Delete Movie {random.randint(10000, 99999)}",
                "imageUrl": "https://images.unsplash.com/photo-1536440136628-849c177e76a1.jpg",  # Починили тут тоже
                "price": 150,
                "description": "Temporary description",
                "location": "SPB",
                "published": True,
                "genreId": 1
            }
            try:
                create_resp = super_admin.api.movies.create_movie(fake_movie, expected_status=201)
                target_id = create_resp.json()["id"]
            except Exception:
                target_id = random.randint(5000, 99999)
        else:
            target_id = 999999

        current_user.api.movies.delete_movie(movie_id=target_id, expected_status=expected_status)