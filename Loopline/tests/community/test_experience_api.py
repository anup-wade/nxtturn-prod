import pytest
from django.urls import reverse
from rest_framework import status
from community.models import Experience

# Mark all tests in this file as requiring database access
pytestmark = pytest.mark.django_db


@pytest.fixture
def experience_payload():
    """
    Provides a valid payload for creating/updating an experience entry.
    """
    return {
        "title": "Senior Developer",
        "company": "Tech Corp",
        "location": "New York, NY",
        "start_date": "2020-01-01",
        "end_date": "2022-01-01",
        "description": "Led the backend team.",
    }


class TestExperienceAPI:
    """
    Test suite for the /api/profile/experience/ endpoint.
    """

    def test_unauthenticated_user_cannot_access_experience_endpoints(self, api_client):
        """
        Verifies that all experience endpoints are protected and require authentication.
        """
        list_create_url = reverse("community:profile-experience-list")
        # Assume an entry with pk=1 might exist; the endpoint should be protected regardless.
        detail_url = reverse("community:profile-experience-detail", kwargs={"pk": 1})

        response_get = api_client.get(list_create_url)
        response_post = api_client.post(list_create_url, {})
        response_patch = api_client.patch(detail_url, {})
        response_delete = api_client.delete(detail_url)

        assert response_get.status_code == status.HTTP_401_UNAUTHORIZED
        assert response_post.status_code == status.HTTP_401_UNAUTHORIZED
        assert response_patch.status_code == status.HTTP_401_UNAUTHORIZED
        assert response_delete.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_can_create_experience_entry(
        self, api_client_factory, user_factory, experience_payload
    ):
        """
        Tests that an authenticated user can successfully add an experience entry to their profile.
        """
        user = user_factory()
        client = api_client_factory(user=user)
        url = reverse("community:profile-experience-list")

        response = client.post(url, data=experience_payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Experience.objects.count() == 1

        # Verify the created object is linked to the correct user profile
        created_entry = Experience.objects.first()
        assert created_entry.user_profile == user.profile
        assert response.data["title"] == experience_payload["title"]
        assert response.data["company"] == experience_payload["company"]

    def test_user_can_create_current_job_entry(
        self, api_client_factory, user_factory, experience_payload
    ):
        """
        Tests that a user can create a 'Current' job (end_date is null).
        """
        user = user_factory()
        client = api_client_factory(user=user)
        url = reverse("community:profile-experience-list")

        # Set end_date to None (implies "Present")
        experience_payload["end_date"] = None

        response = client.post(url, data=experience_payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["end_date"] is None

        created_entry = Experience.objects.first()
        assert created_entry.end_date is None

    def test_user_can_list_only_their_own_experience(
        self, api_client_factory, user_factory, experience_payload
    ):
        """
        Tests that the LIST endpoint only returns experience entries belonging to the authenticated user.
        """
        user_a = user_factory(username="user_a")
        user_b = user_factory(username="user_b")

        # Create an experience entry for User A directly in DB
        Experience.objects.create(user_profile=user_a.profile, **experience_payload)

        # Authenticate as User B
        client_b = api_client_factory(user=user_b)
        url = reverse("community:profile-experience-list")
        response_b = client_b.get(url)

        # User B should see an empty list
        assert response_b.status_code == status.HTTP_200_OK
        assert response_b.data["count"] == 0
        assert len(response_b.data["results"]) == 0

        # Authenticate as User A
        client_a = api_client_factory(user=user_a)
        response_a = client_a.get(url)

        # User A should see their one entry
        assert response_a.status_code == status.HTTP_200_OK
        assert response_a.data["count"] == 1
        assert len(response_a.data["results"]) == 1
        assert response_a.data["results"][0]["title"] == experience_payload["title"]

    def test_user_can_update_their_own_experience_entry(
        self, api_client_factory, user_factory, experience_payload
    ):
        """
        Tests that a user can successfully update one of their own experience entries.
        """
        user = user_factory()
        entry = Experience.objects.create(
            user_profile=user.profile, **experience_payload
        )
        client = api_client_factory(user=user)
        url = reverse("community:profile-experience-detail", kwargs={"pk": entry.pk})

        update_payload = {"title": "Lead Developer"}
        response = client.patch(url, data=update_payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Lead Developer"

        entry.refresh_from_db()
        assert entry.title == "Lead Developer"

    def test_user_can_delete_their_own_experience_entry(
        self, api_client_factory, user_factory, experience_payload
    ):
        """
        Tests that a user can successfully delete one of their own experience entries.
        """
        user = user_factory()
        entry = Experience.objects.create(
            user_profile=user.profile, **experience_payload
        )
        client = api_client_factory(user=user)
        url = reverse("community:profile-experience-detail", kwargs={"pk": entry.pk})

        assert Experience.objects.count() == 1
        response = client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Experience.objects.count() == 0

    def test_user_cannot_modify_another_users_experience(
        self, api_client_factory, user_factory, experience_payload
    ):
        """
        CRITICAL: Verifies that a user cannot retrieve, update, or delete an experience
        entry that does not belong to them.
        """
        owner_user = user_factory(username="owner")
        attacker_user = user_factory(username="attacker")

        # Create an entry owned by 'owner_user'
        entry = Experience.objects.create(
            user_profile=owner_user.profile, **experience_payload
        )

        # Authenticate as the 'attacker_user'
        attacker_client = api_client_factory(user=attacker_user)
        url = reverse("community:profile-experience-detail", kwargs={"pk": entry.pk})

        # Attacker tries to retrieve the entry
        response_get = attacker_client.get(url)
        # Should return 404 because the viewset filters the queryset by request.user
        assert response_get.status_code == status.HTTP_404_NOT_FOUND

        # Attacker tries to update the entry
        response_patch = attacker_client.patch(
            url, data={"title": "Hacked"}, format="json"
        )
        assert response_patch.status_code == status.HTTP_404_NOT_FOUND

        # Attacker tries to delete the entry
        response_delete = attacker_client.delete(url)
        assert response_delete.status_code == status.HTTP_404_NOT_FOUND

        # Verify the original data was not changed
        entry.refresh_from_db()
        assert entry.title == experience_payload["title"]
        assert Experience.objects.count() == 1

    def test_validate_start_date_before_end_date(
        self, api_client_factory, user_factory, experience_payload
    ):
        """
        Tests that the API rejects an entry where the start_date is after the end_date.
        """
        user = user_factory()
        client = api_client_factory(user=user)
        url = reverse("community:profile-experience-list")

        # Set invalid dates: Start 2022, End 2020
        experience_payload["start_date"] = "2022-01-01"
        experience_payload["end_date"] = "2020-01-01"

        response = client.post(url, data=experience_payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "end_date" in response.data
