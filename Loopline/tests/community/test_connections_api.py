# C:\Users\Vinay\Project\Loopline\tests\community\test_connections_api.py

import pytest
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from community.models import ConnectionRequest, Follow

from tests.conftest import user_factory, api_client_factory

User = get_user_model()
pytestmark = pytest.mark.django_db

# ===================================================================
# Tests for ConnectionRequestViewSet (These remain largely unchanged)
# ===================================================================

def test_user_can_send_connection_request(user_factory, api_client_factory):
    sender = user_factory()
    receiver = user_factory()
    client = api_client_factory(user=sender)
    url = reverse('community:connection-request-list')
    payload = {'receiver': receiver.id}
    response = client.post(url, payload)
    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert ConnectionRequest.objects.count() == 1
    request = ConnectionRequest.objects.first()
    assert request.sender == sender
    assert request.receiver == receiver
    assert request.status == 'pending'
    # --- NEW ASSERTION ---
    # Verify that sending a request does NOT automatically create a follow.
    assert not Follow.objects.filter(follower=sender, following=receiver).exists()


def test_user_can_list_received_connection_requests(user_factory, api_client_factory):
    user_a = user_factory()
    user_b = user_factory()
    ConnectionRequest.objects.create(sender=user_a, receiver=user_b, status='pending')
    user_c = user_factory()
    ConnectionRequest.objects.create(sender=user_a, receiver=user_c, status='pending')
    client = api_client_factory(user=user_b)
    url = reverse('community:connection-request-list')
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    results = response_data['results']
    assert response_data['count'] == 1
    assert len(results) == 1
    request_data = results[0]
    assert request_data['sender']['id'] == user_a.id
    assert request_data['status'] == 'pending'  


def test_user_can_accept_connection_request(user_factory, api_client_factory):
    user_a = user_factory()
    user_b = user_factory()
    request_obj = ConnectionRequest.objects.create(sender=user_a, receiver=user_b)
    client = api_client_factory(user=user_b)
    url = reverse('community:connection-request-accept', kwargs={'pk': request_obj.id})
    response = client.post(url)
    assert response.status_code == status.HTTP_200_OK
    request_obj.refresh_from_db()
    assert request_obj.status == 'accepted'
    # Accepting a request MUST create a mutual follow.
    assert Follow.objects.filter(follower=user_a, following=user_b).exists()
    assert Follow.objects.filter(follower=user_b, following=user_a).exists()


def test_user_can_reject_connection_request(user_factory, api_client_factory):
    user_a = user_factory()
    user_b = user_factory()
    request_obj = ConnectionRequest.objects.create(sender=user_a, receiver=user_b)
    client = api_client_factory(user=user_b)
    url = reverse('community:connection-request-reject', kwargs={'pk': request_obj.id})
    response = client.post(url)
    assert response.status_code == status.HTTP_200_OK
    request_obj.refresh_from_db()
    assert request_obj.status == 'rejected'
    # Rejecting a request must NOT create any follows.
    assert not Follow.objects.filter(follower=user_b, following=user_a).exists()


# ===================================================================
# --- REFACTORED TESTS for new FollowToggleView logic ---
# ===================================================================

def test_follow_creates_connection_if_reciprocal_follow_exists(user_factory, api_client_factory):
    """
    Tests: User A follows User B, who is already following A.
    Result: They should become connected.
    """
    user_a = user_factory()
    user_b = user_factory()
    # Pre-condition: User B already follows User A
    Follow.objects.create(follower=user_b, following=user_a)
    
    client = api_client_factory(user=user_a)
    url = reverse('community:follow-toggle', kwargs={'username': user_b.username})
    
    # Action: User A follows User B
    response = client.post(url)

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "connected"}
    assert Follow.objects.filter(follower=user_a, following=user_b).exists()
    assert Follow.objects.filter(follower=user_b, following=user_a).exists()


def test_follow_back_on_pending_request_creates_connection(user_factory, api_client_factory):
    """
    Tests: User B follows User A, who has a pending request to B.
    Result: They should become connected, and the request should be accepted.
    """
    user_a = user_factory()
    user_b = user_factory()
    # Pre-condition: User A has a pending request to User B
    request_obj = ConnectionRequest.objects.create(sender=user_a, receiver=user_b, status='pending')
    
    client = api_client_factory(user=user_b)
    url = reverse('community:follow-toggle', kwargs={'username': user_a.username})

    # Action: User B follows User A
    response = client.post(url)
    
    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "connected"}
    
    request_obj.refresh_from_db()
    assert request_obj.status == 'accepted'
    assert Follow.objects.filter(follower=user_b, following=user_a).exists()
    assert Follow.objects.filter(follower=user_a, following=user_b).exists()


def test_unfollow_breaks_mutual_connection_fully(user_factory, api_client_factory):
    """
    Tests: User B, who is connected to User A, unfollows A.
    Result: The connection is fully broken (both follows are deleted) and the
            ConnectionRequest is reset.
    """
    user_a = user_factory()
    user_b = user_factory()
    # Pre-condition: A and B are connected (mutual follow, accepted request)
    Follow.objects.create(follower=user_a, following=user_b)
    Follow.objects.create(follower=user_b, following=user_a)
    request_obj = ConnectionRequest.objects.create(sender=user_a, receiver=user_b, status='accepted')
    
    client = api_client_factory(user=user_b)
    url = reverse('community:follow-toggle', kwargs={'username': user_a.username})

    # Action: User B unfollows User A
    response = client.delete(url)
    
    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "disconnected"}
    
    request_obj.refresh_from_db()
    assert request_obj.status == 'rejected' # Verify connection is marked as broken
    
    # Verify BOTH follows have been deleted
    assert not Follow.objects.filter(follower=user_b, following=user_a).exists()
    assert not Follow.objects.filter(follower=user_a, following=user_b).exists()


# ===================================================================
# --- DEPRECATED TestRelationshipStatusAPI ---
# The UserRelationshipView has been removed. These tests are now obsolete
# and their logic is covered by the tests in test_profile_api.py.
# ===================================================================

# (The entire TestRelationshipStatusAPI class has been removed)