# C:\Users\Vinay\Project\Loopline\tests\conftest.py

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from community.models import Group, GroupJoinRequest
from channels.layers import get_channel_layer
from allauth.account.models import EmailAddress  # <--- 1. ADD THIS IMPORT

User = get_user_model()

@pytest.fixture
def user_factory(db):
    """
    A robust factory that can create users in multiple ways.
    It ALWAYS creates a valid, email-verified user.
    """
    def create_user(
        username=None,
        password='password123',
        username_prefix='user',
        **kwargs
    ):
        if not username:
            if not hasattr(create_user, "counter"):
                create_user.counter = 0
            create_user.counter += 1
            username = f"{username_prefix}_{create_user.counter}"
        
        email = kwargs.pop('email', f'{username}@test.com')
        
        # Part 1: Create the standard Django user (this part is unchanged)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            **kwargs
        )

        # <--- 2. ADD THIS CRITICAL BLOCK ---
        # Programmatically create a verified email address for the user,
        # which is now required for logging in due to mandatory verification.
        EmailAddress.objects.create(
            user=user,
            email=user.email,
            primary=True,
            verified=True
        )
        # --- END OF THE NEW BLOCK ---

        return user
    
    create_user.counter = 0
    return create_user

# --- All other fixtures remain unchanged ---
@pytest.fixture
def api_client_factory(db):
    def create_client(user=None):
        client = APIClient()
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        return client
    return create_client

@pytest.fixture
def api_client(api_client_factory):
    return api_client_factory()
    
@pytest.fixture
def join_request_scenario(user_factory):
    creator = user_factory(username='creator')
    requester = user_factory(username='requester')
    private_group = Group.objects.create(
        creator=creator, 
        name="Exclusive Test Group", 
        privacy_level='private'
    )
    join_request = GroupJoinRequest.objects.create(
        user=requester, 
        group=private_group, 
        status='pending'
    )
    return {
        'creator': creator,
        'requester': requester,
        'group': private_group,
        'request': join_request
    }

@pytest.fixture
def channel_layer():
    return get_channel_layer()