# C:\Users\Vinay\Project\Loopline\tests\community\test_profile_api.py

import pytest
from rest_framework import status
from django.urls import reverse
from community.models import Follow, ConnectionRequest

pytestmark = pytest.mark.django_db


def test_unauthenticated_user_can_view_profile(api_client, user_factory):
    profile_user = user_factory(username="testprofile")
    url = reverse(
        "community:userprofile-detail", kwargs={"username": profile_user.username}
    )
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["user"]["username"] == "testprofile"
    assert response.data["relationship_status"] is None


def test_profile_returns_correct_relationship_status_no_relationship(
    api_client_factory, user_factory
):
    profile_user = user_factory()
    viewer_user = user_factory()
    client = api_client_factory(user=viewer_user)
    url = reverse(
        "community:userprofile-detail", kwargs={"username": profile_user.username}
    )
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    expected_status = {
        "connection_status": "not_connected",
        "is_followed_by_request_user": False,
    }
    assert response.data["relationship_status"] == expected_status


def test_profile_returns_correct_relationship_status_viewer_follows(
    api_client_factory, user_factory
):
    profile_user = user_factory()
    viewer_user = user_factory()
    Follow.objects.create(follower=viewer_user, following=profile_user)
    client = api_client_factory(user=viewer_user)
    url = reverse(
        "community:userprofile-detail", kwargs={"username": profile_user.username}
    )
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    expected_status = {
        "connection_status": "not_connected",
        "is_followed_by_request_user": True,
    }
    assert response.data["relationship_status"] == expected_status


def test_profile_returns_correct_relationship_status_request_sent(
    api_client_factory, user_factory
):
    profile_user = user_factory()
    viewer_user = user_factory()
    ConnectionRequest.objects.create(
        sender=viewer_user, receiver=profile_user, status="pending"
    )
    client = api_client_factory(user=viewer_user)
    url = reverse(
        "community:userprofile-detail", kwargs={"username": profile_user.username}
    )
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    expected_status = {
        "connection_status": "request_sent",
        "is_followed_by_request_user": False,
    }
    assert response.data["relationship_status"] == expected_status


def test_profile_returns_correct_relationship_status_request_received(
    api_client_factory, user_factory
):
    profile_user = user_factory()
    viewer_user = user_factory()
    ConnectionRequest.objects.create(
        sender=profile_user, receiver=viewer_user, status="pending"
    )
    client = api_client_factory(user=viewer_user)
    url = reverse(
        "community:userprofile-detail", kwargs={"username": profile_user.username}
    )
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    expected_status = {
        "connection_status": "request_received",
        "is_followed_by_request_user": False,
    }
    assert response.data["relationship_status"] == expected_status


def test_profile_returns_correct_relationship_status_connected(
    api_client_factory, user_factory
):
    profile_user = user_factory()
    viewer_user = user_factory()
    Follow.objects.create(follower=viewer_user, following=profile_user)
    Follow.objects.create(follower=profile_user, following=viewer_user)
    client = api_client_factory(user=viewer_user)
    url = reverse(
        "community:userprofile-detail", kwargs={"username": profile_user.username}
    )
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    expected_status = {
        "connection_status": "connected",
        "is_followed_by_request_user": True,
    }
    assert response.data["relationship_status"] == expected_status


def test_user_cannot_update_another_users_profile(api_client_factory, user_factory):
    profile_owner = user_factory(username="owner")
    attacker = user_factory(username="attacker")
    client = api_client_factory(user=attacker)
    url = reverse(
        "community:userprofile-detail", kwargs={"username": profile_owner.username}
    )
    payload = {"bio": "Trying to hack this profile."}
    response = client.patch(url, data=payload, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_unauthenticated_user_cannot_update_profile(api_client, user_factory):
    user = user_factory(username="testuser")
    url = reverse("community:userprofile-detail", kwargs={"username": user.username})
    payload = {"bio": "Anonymous update attempt."}
    response = api_client.patch(url, data=payload, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_can_follow_another_user(user_factory, api_client_factory):
    user_a = user_factory()
    user_b = user_factory()
    client = api_client_factory(user=user_a)
    url = reverse("community:follow-toggle", kwargs={"username": user_b.username})
    response = client.post(url)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"status": "following"}
    assert Follow.objects.filter(follower=user_a, following=user_b).exists()


def test_user_can_unfollow_another_user(user_factory, api_client_factory):
    user_a = user_factory()
    user_b = user_factory()
    Follow.objects.create(follower=user_a, following=user_b)
    client = api_client_factory(user=user_a)
    url = reverse("community:follow-toggle", kwargs={"username": user_b.username})
    response = client.delete(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "unfollowed"}
    assert not Follow.objects.filter(follower=user_a, following=user_b).exists()
