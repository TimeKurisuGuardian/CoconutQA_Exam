from custom_requester.custom_requester import CustomRequester
from config.base_urls import MOVIES_BASE_URL

MOVIES = '/movies'


class MoviesApi(CustomRequester):
    def __init__(self, session):
        super().__init__(session=session, base_url=MOVIES_BASE_URL)

    def get_movies(self, params=None, expected_status=200, **kwargs):
        return self.send_request(
            method="GET",
            endpoint=MOVIES,
            params=params,
            expected_status=expected_status,
            **kwargs
        )

    def create_movie(self, movie_data, expected_status=201, **kwargs):
        # Явно передаем expected_status в send_request
        return self.send_request(
            method="POST",
            endpoint=MOVIES,
            data=movie_data,
            expected_status=expected_status,
            **kwargs
        )

    def update_movie(self, movie_id, movie_data, expected_status=200, **kwargs):
        # Явно передаем expected_status в send_request
        return self.send_request(
            method="PATCH",
            endpoint=f"{MOVIES}/{movie_id}",
            data=movie_data,
            expected_status=expected_status,
            **kwargs
        )

    def delete_movie(self, movie_id, expected_status=200, **kwargs):
        return self.send_request(
            method="DELETE",
            endpoint=f"{MOVIES}/{movie_id}",
            expected_status=expected_status,
            **kwargs
        )