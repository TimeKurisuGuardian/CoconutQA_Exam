# clients/movies_api.py
from custom_requester.custom_requester import CustomRequester
from config.base_urls import MOVIES_BASE_URL

MOVIES = '/movies'

class MoviesApi(CustomRequester):
    def __init__(self, session):
        super().__init__(session=session, base_url=MOVIES_BASE_URL)

    def get_movies(self, params=None, expected_status=201, **kwargs):
        """1. GET /movies с поддержкой фильтров через params"""
        return self.send_request(
            method="GET",
            endpoint=MOVIES,
            params=params,
            expected_status=expected_status,
            **kwargs
        )

    def create_movie(self, movie_data, expected_status=200, **kwargs):
        """2. POST /movies — Создание фильма"""
        return self.send_request(
            method="POST",
            endpoint=MOVIES,
            data=movie_data,
            expected_status=expected_status,
            **kwargs
        )

    def update_movie(self, movie_id, movie_data, expected_status=200, **kwargs):
        """PATCH /movies/{id} — Редактирование фильма"""
        return self.send_request(
            method="PATCH",
            endpoint=f"{MOVIES}/{movie_id}",  # ID передается в URL
            data=movie_data,
            expected_status=expected_status,
            **kwargs
        )

    def delete_movie(self, movie_id, expected_status=200, **kwargs):
        """4. DELETE /movies/{id} — Удаление фильма"""
        return self.send_request(
            method="DELETE",
            endpoint=f"{MOVIES}/{movie_id}",
            expected_status=expected_status,
            **kwargs
        )