# C:\Users\Vinay\Project\Loopline\tests\community\test_about_tab_api.py

import pytest
from rest_framework import status
from django.urls import reverse
from community.models import SocialLink

pytestmark = pytest.mark.django_db


def test_user_can_update_own_profile(api_client_factory, user_factory):
    """
    Tests that a user can update their own profile with the new
    structured location data and bio.
    """
    user = user_factory(username="editor")
    client = api_client_factory(user=user)
    url = reverse("community:userprofile-detail", kwargs={"username": user.username})

    payload = {
        "bio": "This is my new bio.",
        "location_city": "New York",
        "location_administrative_area": "NY",
        "location_country": "USA",
        "current_work_style": "remote",
        "is_open_to_relocation": True,
    }

    response = client.patch(url, data=payload, format="json")

    # ASSERT: Check the response status and data
    assert response.status_code == status.HTTP_200_OK
    assert response.data["bio"] == "This is my new bio."
    assert response.data["location_city"] == "New York"
    assert response.data["current_work_style"] == "remote"
    assert response.data["is_open_to_relocation"] is True

    # ASSERT: Check the database state (most important)
    user.profile.refresh_from_db()
    assert user.profile.bio == "This is my new bio."
    assert user.profile.location_city == "New York"
    assert user.profile.location_administrative_area == "NY"
    assert user.profile.location_country == "USA"
    assert user.profile.current_work_style == "remote"
    assert user.profile.is_open_to_relocation is True


def test_user_can_update_social_links(api_client_factory, user_factory):
    """
    Tests the full create, update, and delete lifecycle for SocialLink objects
    via a single PATCH request to the user's profile.
    """
    user = user_factory(username="linker")
    profile = user.profile
    client = api_client_factory(user=user)

    # ARRANGE: Create some initial links in the database
    link_to_update = SocialLink.objects.create(
        profile=profile, link_type="linkedin", url="https://linkedin.com/old"
    )
    link_to_delete = SocialLink.objects.create(
        profile=profile, link_type="twitter", url="https://twitter.com/old"
    )

    url = reverse("community:userprofile-detail", kwargs={"username": user.username})

    payload = {
        "social_links": [
            {"link_type": "linkedin", "url": "https://linkedin.com/new-and-updated"},
            {"link_type": "github", "url": "https://github.com/new"},
        ]
    }

    # ACT: Make the API call
    response = client.patch(url, data=payload, format="json")

    # ASSERT: Check the response
    assert response.status_code == status.HTTP_200_OK

    # ASSERT: Check the database state
    profile.refresh_from_db()

    assert profile.social_links.count() == 2
    assert not SocialLink.objects.filter(id=link_to_delete.id).exists()
    assert not SocialLink.objects.filter(id=link_to_update.id).exists()
    assert profile.social_links.filter(
        link_type="linkedin", url="https://linkedin.com/new-and-updated"
    ).exists()
    assert profile.social_links.filter(
        link_type="github", url="https://github.com/new"
    ).exists()
