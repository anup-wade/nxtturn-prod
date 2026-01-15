# C:\Users\Vinay\Project\Loopline\tests\community\test_saved_post_api.py
import pytest
from rest_framework import status
from community.models import StatusPost

# This line tells Pylance that these fixtures are available.
from tests.conftest import user_factory, api_client_factory, api_client

pytestmark = pytest.mark.django_db

def test_user_can_toggle_saved_post(user_factory, api_client_factory):
    """
    Verifies a user can save and then unsave a post via the API.
    """
    # Arrange
    post_owner = user_factory()
    saver = user_factory()
    post = StatusPost.objects.create(author=post_owner, content="A post to be saved.")
    client = api_client_factory(user=saver)
    save_url = f'/api/posts/{post.id}/save/'

    # --- ACTION 1: SAVE THE POST ---
    assert saver.profile.saved_posts.count() == 0
    response_save = client.post(save_url)

    # Assert (SAVE)
    assert response_save.status_code == status.HTTP_200_OK
    assert saver.profile.saved_posts.count() == 1
    assert saver.profile.saved_posts.first() == post
    assert response_save.json()['is_saved'] == True

    # --- ACTION 2: UNSAVE THE POST ---
    response_unsave = client.post(save_url)

    # Assert (UNSAVE)
    assert response_unsave.status_code == status.HTTP_200_OK
    assert saver.profile.saved_posts.count() == 0
    assert response_unsave.json()['is_saved'] == False

def test_user_can_list_own_saved_posts(user_factory, api_client_factory):
    """
    Verifies that the saved posts endpoint only returns posts saved
    by the authenticated user, isolating from other users' saved posts.
    """
    # Arrange: We need two users to ensure data is properly isolated.
    user_a = user_factory()
    user_b = user_factory()
    post_1 = StatusPost.objects.create(author=user_a, content="Post number 1.")
    post_2 = StatusPost.objects.create(author=user_b, content="Post number 2.")
    
    # User A saves post 2. User B saves post 1.
    user_a.profile.saved_posts.add(post_2)
    user_b.profile.saved_posts.add(post_1)
    
    # Authenticate as User A.
    client = api_client_factory(user=user_a)

    # Act: User A requests their list of saved posts.
    response = client.get('/api/posts/saved/')

    # Assert
    assert response.status_code == status.HTTP_200_OK
    results = response.json()['results']
    
    # The API should return exactly one post.
    assert len(results) == 1
    
    # That one post must be post_2, which is the one User A saved.
    saved_post = results[0]
    assert saved_post['id'] == post_2.id