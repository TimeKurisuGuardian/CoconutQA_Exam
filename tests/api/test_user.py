# tests/api/test_user.py

def test_get_user_info_unauthorized(unauthenticated_api_manager):
    unauthenticated_api_manager.user_api.get_user_info(
        user_id="123",
        expected_status=401
    )


def test_get_user_info_success(api_manager, authenticated_user):
    """ПОЛНАЯ ЗАДАЧА: Проверяем получение инфо под авторизованным юзером"""
    # Фикстура authenticated_user уже закинула токен в api_manager!
    user_id = authenticated_user["id"]

    # Делаем запрос профиля
    response = api_manager.user_api.get_user_info(user_id=user_id)
    response_data = response.json()

    # Сверяем данные в ответе (assert)
    assert response.status_code == 200
    assert response_data["email"] == authenticated_user["email"]
    assert response_data["id"] == user_id