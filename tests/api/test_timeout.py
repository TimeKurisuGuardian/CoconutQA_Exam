import pytest
import requests

def test_register_timeout(api_manager, test_user):
    # requests.exceptions.Timeout поймает И connect timeout, И read timeout!
    with pytest.raises(requests.exceptions.Timeout):
        api_manager.auth_api.register_user(test_user, timeout=0.001)