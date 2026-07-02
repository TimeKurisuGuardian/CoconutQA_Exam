# clients/user_api.py
from custom_requester.custom_requester import CustomRequester
from config.base_urls import AUTH_BASE_URL

USER = '/user'

class UserApi(CustomRequester):
    def __init__(self, session, base_url=AUTH_BASE_URL):
        super().__init__(session=session, base_url=base_url)

    def get_user_info(self, user_id, expected_status=200, **kwargs):
        return self.send_request(
            method="GET",
            endpoint=f"{USER}/{user_id}",
            expected_status=expected_status,
            **kwargs
        )

    def delete_user(self, user_id, expected_status=200, **kwargs):
        return self.send_request(
            method="DELETE",
            endpoint=f"{USER}/{user_id}",
            expected_status=expected_status,
            **kwargs
        )

    # ЗАДАЧА 3: Массовое удаление через *args
    def delete_users(self, *user_ids, **kwargs):
        for user_id in user_ids:
            # вызываем наш же одиночный метод для каждого id
            self.delete_user(user_id, **kwargs)

    def create_user(self, user_data, expected_status=201):
        """Создание нового пользователя админом (POST /user)"""
        return self.send_request(
            method="POST",
            endpoint=f"{USER}",
            data=user_data,
            expected_status=expected_status
        )