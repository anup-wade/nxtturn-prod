# C:\Users\Vinay\Project\Loopline\tests\community\test_registration_api.py
import pytest
from rest_framework import status
from django.contrib.auth import get_user_model

# Note: The conftest.py file automatically provides the 'api_client' and 'user_factory' fixtures.
# We don't need to import them directly here.

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_user_registration_success(api_client):
    """
    Ensures a new user can be registered successfully via the API
    with the correct password1 and password2 fields.
    """
    registration_data = {
        'username': 'newtestuser',
        'email': 'newtestuser@example.com',
        'password1': 'StrongPassword123',
        'password2': 'StrongPassword123'
    }
    url = '/api/auth/registration/'
    response = api_client.post(url, registration_data)
    assert response.status_code == status.HTTP_201_CREATED, \
        f"Expected status 201, but got {response.status_code}. Response: {response.data}"
    assert User.objects.filter(username='newtestuser').exists()


def test_user_registration_fails_with_mismatched_passwords(api_client):
    """
    Ensures registration fails if password1 and password2 do not match.
    """
    registration_data = {
        'username': 'anotheruser',
        'email': 'another@example.com',
        'password1': 'StrongPassword123',
        'password2': 'DIFFERENTPassword123'
    }
    url = '/api/auth/registration/'
    response = api_client.post(url, registration_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'non_field_errors' in response.data
    assert "The two password fields didn't match." in response.data['non_field_errors'][0]
    assert not User.objects.filter(username='anotheruser').exists()


def test_user_registration_fails_with_existing_username(api_client, user_factory):
    """
    Ensures registration fails if the username is already taken.
    """
    existing_user = user_factory(username_prefix="existinguser")
    registration_data = {
        'username': existing_user.username,
        'email': 'newemail@example.com',
        'password1': 'StrongPassword123',
        'password2': 'StrongPassword123'
    }
    url = '/api/auth/registration/'
    response = api_client.post(url, registration_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'username' in response.data
    assert 'A user with that username already exists.' in response.data['username'][0]


def test_registration_fails_with_duplicate_email(api_client):
    """
    Ensures registration fails if the email address is already in use,
    even with a different username.
    """
    url = '/api/auth/registration/'
    user1_data = {
        "username": "user1_unique",
        "email": "duplicate_test@example.com",
        "password1": "StrongPassword123",
        "password2": "StrongPassword123"
    }
    response1 = api_client.post(url, user1_data)
    assert response1.status_code == status.HTTP_201_CREATED, \
        "The first user should have registered successfully to set up the test."
    user2_data = {
        "username": "user2_also_unique",
        "email": "duplicate_test@example.com",
        "password1": "StrongPassword123",
        "password2": "StrongPassword123"
    }
    response2 = api_client.post(url, user2_data)
    assert response2.status_code == status.HTTP_400_BAD_REQUEST, \
        "Expected registration to fail with a 400 status, but it returned 201."
    assert 'email' in response2.data
    assert 'This field must be unique.' in response2.data['email'][0]


# --- THIS IS THE NEW TEST WE ARE ADDING ---
def test_newly_registered_user_cannot_login_before_email_verification(api_client):
    """
    Tests that a user who has just registered cannot log in if email
    verification is mandatory and they have not yet verified their email.
    This test will fail until the corresponding allauth setting is enabled.
    """
    # Step 1: Register a new, unverified user
    registration_data = {
        "username": "unverifieduser",
        "email": "unverified@example.com",
        "password1": "strongpassword123", # Registration requires password1/2
        "password2": "strongpassword123"
    }
    register_url = "/api/auth/registration/"
    response = api_client.post(register_url, registration_data)
    assert response.status_code == status.HTTP_201_CREATED

    # Step 2: Attempt to log in with the new credentials
    login_data = {
        "email": "unverified@example.com",
        "password": "strongpassword123", # Login just requires password
    }
    login_url = "/api/auth/login/"
    login_response = api_client.post(login_url, login_data)

    # Step 3: Assert that the login attempt is rejected
    assert login_response.status_code == status.HTTP_400_BAD_REQUEST
    assert "non_field_errors" in login_response.data
    assert "E-mail is not verified." in str(login_response.data["non_field_errors"])