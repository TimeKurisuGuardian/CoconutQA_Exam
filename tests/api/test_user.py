import pytest

class TestUser:

    def test_create_user(self, super_admin, creation_user_data):

        response = super_admin.api.user_api.create_user(creation_user_data).json()

        assert response.get('id') and response['id'] != '', "ID должен быть не пустым"
        assert response.get('email') == creation_user_data['email']
        assert response.get('fullName') == creation_user_data['fullName']
        assert response.get('verified') is True

    def test_get_user_by_locator(self, super_admin, creation_user_data):
        """Проверка, что созданного юзера можно найти как по ID, ак и по Email"""

        created_user_response = super_admin.api.user_api.create_user(creation_user_data).json()

        response_by_id = super_admin.api.user_api.get_user_info(created_user_response['id']).json()

        response_by_email = super_admin.api.user_api.get_user_info(creation_user_data['email']).json()

        assert response_by_id == response_by_email, "Содержание ответов должно быть идентичным"
        assert response_by_id.get('id') == created_user_response['id']

    def test_get_user_by_id_common_user_forbidden(self, common_user):
        """Негативный: Обычный юзер получает 403 при попытке запросить информацию о юзере"""

        common_user.api.user_api.get_user_info(common_user.email, expected_status=403)