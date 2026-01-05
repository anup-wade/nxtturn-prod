# C:\Users\Vinay\Project\Loopline\tests\community\test_auth_api.py

import pytest
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.core import mail
from allauth.account.models import EmailAddress

# Import the necessary fixtures from your conftest
from tests.conftest import user_factory, api_client_factory

# Mark all tests in this file to use the database
pytestmark = pytest.mark.django_db


def test_user_can_login_with_valid_credentials(user_factory, api_client_factory):
    """
    Verifies that a registered user can log in and receive an auth token.
    """
    password = 'supersecretpassword123'
    user = user_factory(password=password)
    
    # We use an unauthenticated client to perform the login
    client = api_client_factory()
    
    response = client.post('/api/auth/login/', {
        'username': user.username,
        'password': password
    })
    
    assert response.status_code == status.HTTP_200_OK
    assert 'key' in response.json()
    # Verify the token was actually created in the database for this user
    assert Token.objects.filter(user=user).exists()


def test_user_cannot_login_with_invalid_password(user_factory, api_client_factory):
    """
    Verifies that a login attempt with an incorrect password fails.
    """
    password = 'supersecretpassword123'
    user = user_factory(password=password)
    client = api_client_factory()
    
    response = client.post('/api/auth/login/', {
        'username': user.username,
        'password': 'wrongpassword'
    })
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'non_field_errors' in response.json()


def test_user_cannot_login_if_nonexistent(api_client_factory):
    """
    Verifies that a login attempt for a user that does not exist fails.
    """
    client = api_client_factory()
    response = client.post('/api/auth/login/', {
        'username': 'nonexistentuser',
        'password': 'password123'
    })
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_user_can_logout_and_token_is_invalidated(user_factory, api_client_factory):
    """
    Verifies that logging out deletes the user's auth token,
    preventing further authenticated requests.
    """
    user = user_factory()
    # Create an authenticated client, which will have a valid token
    client = api_client_factory(user=user)

    # Sanity check: ensure the user has a token and can access a protected route
    assert Token.objects.filter(user=user).exists()
    user_details_response = client.get('/api/auth/user/')
    assert user_details_response.status_code == status.HTTP_200_OK

    # Perform the logout
    logout_response = client.post('/api/auth/logout/')
    assert logout_response.status_code == status.HTTP_200_OK

    # CRITICAL: Verify the token is now gone from the database
    assert not Token.objects.filter(user=user).exists()
    
    # CRITICAL: Verify that the old client can no longer access protected routes
    user_details_response_after_logout = client.get('/api/auth/user/')
    assert user_details_response_after_logout.status_code == status.HTTP_401_UNAUTHORIZED


def test_unauthenticated_user_cannot_logout(api_client_factory):
    """
    Verifies that the logout endpoint is protected and requires authentication.
    """
    client = api_client_factory()
    response = client.post('/api/auth/logout/')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_login_attempt_for_unverified_user_resends_verification_email(user_factory, api_client_factory):
    """
    Tests that a login attempt with an unverified email address triggers the
    re-sending of the account verification email.
    """
    # Arrange: Create a user and explicitly mark their email as unverified
    password = "testpassword123"
    user = user_factory(password=password)
    email_address = EmailAddress.objects.get(user=user)
    email_address.verified = False
    email_address.save()
    
    # Pre-condition check: Ensure no emails have been sent yet
    assert len(mail.outbox) == 0
    
    # Act: Attempt to log in using the email with an unauthenticated client
    client = api_client_factory()
    response = client.post('/api/auth/login/', {
        'email': user.email,
        'password': password
    })

    # Assert: The login fails, but a new verification email is sent
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert len(mail.outbox) == 1
    
    # Assert: Verify the email was sent to the correct user
    sent_email = mail.outbox[0]
    assert sent_email.to[0] == user.email
    assert "Please Confirm Your Email Address" in sent_email.subject