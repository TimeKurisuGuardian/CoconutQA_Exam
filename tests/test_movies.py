# tests/test_movies.py
import pytest
from utils.data_generator import DataGenerator


@pytest.fixture(scope="function")
def created_movie(api_manager, authenticated_admin):
    """Фикстура: создает фильм под админом перед тестом и удаляет его после"""
    movie_data = DataGenerator.generate_random_movie_data()

    response = api_manager.movies.create_movie(movie_data, expected_status=201)
    movie_json = response.json()

    yield movie_json

    # Удаляем созданный фильм
    api_manager.movies.delete_movie(movie_json["id"], expected_status=200)


class TestMovies:

    def test_get_movies_filter_by_genre(self, api_manager, created_movie):
        """Тест 1: Проверка фильтрации по genreId (GET /movies)"""
        target_genre_id = created_movie["genreId"]

        response = api_manager.movies.get_movies(params={"genreId": target_genre_id}, expected_status=200)
        assert response.status_code == 200

        data = response.json()

        # Разбираем структуру FindAllMoviesResponse
        # Если пришел словарь, ищем список внутри популярных ключей пагинации
        if isinstance(data, dict):
            movies = data.get("results") or data.get("content") or data.get("movies") or data.get("items") or data
        else:
            movies = data

        # Проверяем фильтрацию, если нам вернулся список
        if isinstance(movies, list):
            for movie in movies:
                if isinstance(movie, dict) and "genreId" in movie:
                    assert movie["genreId"] == target_genre_id

    def test_update_movie_positive(self, api_manager, created_movie):
        """Тест 2: Позитивный тест на редактирование фильма под SUPER_ADMIN (PATCH /movies/{id})"""
        movie_id = created_movie["id"]

        # Для PATCH (частичного редактирования) достаточно передать только то поле, которое меняем!
        updated_data = {
            "name": "Pavel's New Cool Movie"
        }

        response = api_manager.movies.update_movie(
            movie_id=movie_id,
            movie_data=updated_data,
            expected_status=200
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Pavel's New Cool Movie"

    def test_delete_movie_negative_not_found(self, api_manager, authenticated_admin):
        """Тест 3: Негативный тест на DELETE несуществующего фильма под админом"""
        invalid_id = 999999
        response = api_manager.movies.delete_movie(movie_id=invalid_id, expected_status=404)
        assert response.status_code == 404

    def test_create_movie_as_regular_user_forbidden(self, api_manager, authenticated_user):
        """Тест 4: Задание 4 — Намеренная ошибка. Ожидается 403 Forbidden для роли USER"""
        fake_movie = DataGenerator.generate_random_movie_data()

        response = api_manager.movies.create_movie(
            movie_data=fake_movie,
            expected_status=403
        )
        assert response.status_code == 403