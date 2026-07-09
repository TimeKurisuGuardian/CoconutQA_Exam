class User:
    """
        Класс, описывающий сущность пользователя в системе.
        Объединяет учетные данные и роли пользователя.
    """

    def __init__(self, email: str, password: str, roles: list):
        self.email = email
        self.password = password
        self.roles = roles

    @property
    def creds(self):
        """Возвращает учетные данные пользователя в виде кортежа(email, password"""
        return self.email, self.password

