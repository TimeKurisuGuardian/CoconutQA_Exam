from clients.api_manager import ApiManager

class User:
    """
    Класс, описывающий сущность пользователя в системе.
    Объединяет учетные данные, роли и персональный экземпляр ApiManager
    для выполнения изолированных запросов.
    """

    def __init__(self, email: str, password: str, roles: list, api: ApiManager):
        self.email = email
        self.password = password
        self.roles = roles
        self.api = api

    @property
    def creds(self):
        """Возвращает учетные данные пользователя в виде кортежа(email, password"""
        return self.email, self.password

