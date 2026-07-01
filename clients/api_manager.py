# clients/api_manager.py
from clients.auth_api import AuthApi
from clients.user_api import UserApi
from clients.movies_api import MoviesApi # Подключаем фильмы

class ApiManager:
    def __init__(self, session):
        self.session = session
        self.auth_api = AuthApi(session)
        self.user_api = UserApi(session)
        self.movies = MoviesApi(session)