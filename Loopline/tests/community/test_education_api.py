# C:\Users\Vinay\Project\Loopline\tests\community\test_education_api.py
# --- THIS IS THE FINAL, CORRECTED VERSION ---

import pytest
from django.urls import reverse
from rest_framework import status
from community.models import Education, UserProfile

# Mark all tests in this file as requiring database access
pytestmark = pytest.mark.django_db


@pytest.fixture
def education_payload():
    """
    Provides a valid payload for creating/updating an education entry.
    This now uses 'start_date' and 'end_date' to match the final model.
    """
    return {
        "institution": "State University",
        "degree": "Bachelor of Science",
        "field_of_study": "Computer Science",
        # CORRECTED: Use the final DateField format
        "start_date": "2018-09-01",
        "end_date": "2022-05-15",
        "description": "Graduated with honors.",
        "location": "New York, NY",
        "achievements": "Dean's List, Capstone Project Winner",
    }


class TestEducationAPI:
    """
    Test suite for the /api/profile/education/ endpoint.
    """

    def test_unauthenticated_user_cannot_access_education_endpoints(self, api_client):
        """
        Verifies that all education endpoints are protected and require authentication.
        """
        list_create_url = reverse("community:profile-education-list")
        # Assume an entry with pk=1 might exist; the endpoint should be protected regardless.
        detail_url = reverse("community:profile-education-detail", kwargs={"pk": 1})

        response_get = api_client.get(list_create_url)
        response_post = api_client.post(list_create_url, {})
        response_patch = api_client.patch(detail_url, {})
        response_delete = api_client.delete(detail_url)

        assert response_get.status_code == status.HTTP_401_UNAUTHORIZED
        assert response_post.status_code == status.HTTP_401_UNAUTHORIZED
        assert response_patch.status_code == status.HTTP_401_UNAUTHORIZED
        assert response_delete.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_can_create_education_entry(
        self, api_client_factory, user_factory, education_payload
    ):
        """
        Tests that an authenticated user can successfully add an education entry to their profile.
        """
        user = user_factory()
        client = api_client_factory(user=user)
        url = reverse("community:profile-education-list")

        response = client.post(url, data=education_payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Education.objects.count() == 1

        # Verify the created object is linked to the correct user profile
        created_entry = Education.objects.first()
        assert created_entry.user_profile == user.profile
        assert response.data["institution"] == education_payload["institution"]
        assert response.data["degree"] == education_payload["degree"]
        # CORRECTED: Assert the date field
        assert response.data["start_date"] == education_payload["start_date"]

    def test_user_can_list_only_their_own_education(
        self, api_client_factory, user_factory, education_payload
    ):
        """
        Tests that the LIST endpoint only returns education entries belonging to the authenticated user.
        """
        user_a = user_factory(username="user_a")
        user_b = user_factory(username="user_b")

        # Create an education entry for User A
        Education.objects.create(user_profile=user_a.profile, **education_payload)

        # Authenticate as User B
        client_b = api_client_factory(user=user_b)
        url = reverse("community:profile-education-list")
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
        assert (
            response_a.data["results"][0]["institution"]
            == education_payload["institution"]
        )

    def test_user_can_update_their_own_education_entry(
        self, api_client_factory, user_factory, education_payload
    ):
        """
        Tests that a user can successfully update one of their own education entries.
        """
        user = user_factory()
        entry = Education.objects.create(user_profile=user.profile, **education_payload)
        client = api_client_factory(user=user)
        url = reverse("community:profile-education-detail", kwargs={"pk": entry.pk})

        update_payload = {"degree": "Master of Science"}
        response = client.patch(url, data=update_payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["degree"] == "Master of Science"

        entry.refresh_from_db()
        assert entry.degree == "Master of Science"

    def test_user_can_delete_their_own_education_entry(
        self, api_client_factory, user_factory, education_payload
    ):
        """
        Tests that a user can successfully delete one of their own education entries.
        """
        user = user_factory()
        entry = Education.objects.create(user_profile=user.profile, **education_payload)
        client = api_client_factory(user=user)
        url = reverse("community:profile-education-detail", kwargs={"pk": entry.pk})

        assert Education.objects.count() == 1
        response = client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Education.objects.count() == 0

    def test_user_cannot_modify_another_users_education(
        self, api_client_factory, user_factory, education_payload
    ):
        """
        CRITICAL: Verifies that a user cannot retrieve, update, or delete an education
        entry that does not belong to them.
        """
        owner_user = user_factory(username="owner")
        attacker_user = user_factory(username="attacker")

        # Create an entry owned by 'owner_user'
        entry = Education.objects.create(
            user_profile=owner_user.profile, **education_payload
        )

        # Authenticate as the 'attacker_user'
        attacker_client = api_client_factory(user=attacker_user)
        url = reverse("community:profile-education-detail", kwargs={"pk": entry.pk})

        # Attacker tries to retrieve the entry
        response_get = attacker_client.get(url)
        assert response_get.status_code == status.HTTP_404_NOT_FOUND

        # Attacker tries to update the entry
        response_patch = attacker_client.patch(
            url, data={"degree": "Hacked"}, format="json"
        )
        assert response_patch.status_code == status.HTTP_404_NOT_FOUND

        # Attacker tries to delete the entry
        response_delete = attacker_client.delete(url)
        assert response_delete.status_code == status.HTTP_404_NOT_FOUND

        # Verify the original data was not changed
        entry.refresh_from_db()
        assert entry.degree == education_payload["degree"]
        assert Education.objects.count() == 1
