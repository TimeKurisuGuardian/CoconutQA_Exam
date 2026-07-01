# tests/api/test_auth.py

class TestAuth:
    def test_register_user(self, api_manager, test_user):
        # Регистрируем через api_manager
        response = api_manager.auth_api.register_user(test_user)
        response_data = response.json()

        assert response.status_code == 201
        assert response_data["email"] == test_user["email"]
        assert "id" in response_data
        assert "USER" in response_data["roles"]

    def test_register_and_login_user(self, api_manager, registered_user):
        login_data = {
            "email": registered_user["email"],
            "password": registered_user["password"]
        }
        response = api_manager.auth_api.login_user(login_data)
        response_data = response.json()

        assert response.status_code == 200
        assert "accessToken" in response_data
        assert response_data["user"]["email"] == registered_user["email"]