# C:\Users\Vinay\Project\Loopline\tests\community\test_poll_api.py
import pytest
import json
from rest_framework import status
from community.models import Group, StatusPost, Poll, PollOption

# This line tells Pylance that these fixtures are available, silencing the warning.
# Pytest doesn't need this, but it makes the editor smarter.
from tests.conftest import user_factory, api_client_factory, api_client

pytestmark = pytest.mark.django_db

# === Main Feed Polls ===

def test_user_can_create_poll_on_main_feed_with_valid_data(user_factory, api_client_factory):
    """
    Verifies an authenticated user can create a poll on the main feed
    (not in a group) when providing a valid question and options.
    """
    # Arrange
    user = user_factory()
    client = api_client_factory(user=user)
    
    poll_dict = {
        "question": "Which frontend framework is best?",
        "options": ["Vue.js", "React", "Svelte"]
    }
    payload = {"poll_data": json.dumps(poll_dict)}
    
    # Act
    response = client.post('/api/posts/', payload, format='json')
    
    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert StatusPost.objects.count() == 1
    new_post = StatusPost.objects.first()
    assert new_post.group is None
    assert hasattr(new_post, 'poll')
    assert new_post.poll.question == poll_dict["question"]
    assert PollOption.objects.count() == 3

def test_user_cannot_create_poll_on_main_feed_with_invalid_data(user_factory, api_client_factory):
    """
    Verifies the API rejects poll creation on the main feed if data is invalid
    (e.g., too few options, empty question).
    """
    # Arrange
    user = user_factory()
    client = api_client_factory(user=user)
    
    # Test with insufficient options
    poll_dict_1 = {"question": "This poll should fail", "options": ["Only one option"]}
    payload_1 = {"poll_data": json.dumps(poll_dict_1)}
    response_1 = client.post('/api/posts/', payload_1, format='json')
    assert response_1.status_code == status.HTTP_400_BAD_REQUEST
    assert "A poll must have at least two options." in str(response_1.data['poll_data'])

    # Test with empty question
    poll_dict_2 = {"question": "   ", "options": ["Option A", "Option B"]}
    payload_2 = {"poll_data": json.dumps(poll_dict_2)}
    response_2 = client.post('/api/posts/', payload_2, format='json')
    assert response_2.status_code == status.HTTP_400_BAD_REQUEST
    assert "Poll question cannot be empty." in str(response_2.data['poll_data'])

    assert StatusPost.objects.count() == 0

# === Group Polls ===

def test_group_member_can_create_poll_in_group_with_valid_data(user_factory, api_client_factory):
    """
    Verifies an authenticated group member can successfully create a poll post
    inside a group they belong to.
    """
    # Arrange
    creator = user_factory()
    group = Group.objects.create(creator=creator, name="Polling Group")
    group.members.add(creator)
    client = api_client_factory(user=creator)
    
    poll_dict = {
        "question": "Best feature of DRF?",
        "options": ["Serializers", "Viewsets", "Permissions"]
    }
    payload = {
        "group": group.slug,
        "poll_data": json.dumps(poll_dict) 
    }
    
    # Act
    response = client.post('/api/posts/', payload, format='json')
    
    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert StatusPost.objects.count() == 1
    new_post = StatusPost.objects.first()
    assert new_post.group == group
    assert hasattr(new_post, 'poll')
    assert new_post.poll.question == poll_dict["question"]

def test_non_group_member_cannot_create_poll_in_group(user_factory, api_client_factory):
    """
    Verifies a user who is NOT a member of a group receives a 403 Forbidden
    error when trying to create a poll within that group.
    """
    # Arrange
    creator = user_factory()
    non_member = user_factory()
    group = Group.objects.create(creator=creator, name="Private Polling")
    client = api_client_factory(user=non_member)

    poll_dict = {"question": "This should be forbidden", "options": ["Yes", "No"]}
    payload = {"group": group.slug, "poll_data": json.dumps(poll_dict)}

    # Act
    response = client.post('/api/posts/', payload, format='json')
    
    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert StatusPost.objects.count() == 0