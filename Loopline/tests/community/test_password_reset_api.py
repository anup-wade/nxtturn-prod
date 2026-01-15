# C:\Users\Vinay\Project\Loopline\tests\community\test_password_reset_api.py

import pytest
from django.core import mail
from rest_framework import status
from django.contrib.auth import get_user_model

# Import the correct allauth tools
from allauth.account.utils import user_pk_to_url_str
from allauth.account.forms import default_token_generator

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestPasswordResetAPI:
    
    reset_url = "/api/auth/password/reset/"
    confirm_url = "/api/auth/password/reset/confirm/"

    def test_user_can_request_password_reset(self, user_factory, api_client):
        user = user_factory()
        response = api_client.post(self.reset_url, {"email": user.email})
        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 1

    def test_password_reset_request_fails_for_nonexistent_email(self, api_client):
        non_existent_email = "ghost@example.com"
        response = api_client.post(self.reset_url, {"email": non_existent_email})
        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 0

    def test_user_can_successfully_reset_password_with_valid_token(self, user_factory, api_client):
        user = user_factory()
        token = default_token_generator.make_token(user)
        uid = user_pk_to_url_str(user)
        
        new_password = "a-new-secure-password-456"
        payload = {
            "uid": uid,
            "token": token,
            "new_password1": new_password,
            "new_password2": new_password
        }
        
        response = api_client.post(self.confirm_url, payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "Password has been reset with the new password."

        user.refresh_from_db()
        assert user.check_password(new_password) is True