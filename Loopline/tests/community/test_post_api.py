import pytest
from rest_framework import status
from community.models import StatusPost
from tests.conftest import user_factory, api_client_factory, api_client

pytestmark = pytest.mark.django_db

def test_unauthenticated_user_cannot_list_posts(api_client):
    response = api_client.get('/api/posts/')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_authenticated_user_can_list_posts(user_factory, api_client_factory):
    user = user_factory()
    client = api_client_factory(user=user)
    response = client.get('/api/posts/')
    assert response.status_code == status.HTTP_200_OK

def test_post_list_returns_correct_data(user_factory, api_client_factory):
    user = user_factory()
    client = api_client_factory(user=user)
    StatusPost.objects.create(author=user, content="Find me.")
    response = client.get('/api/posts/')
    assert len(response.json()['results']) == 1
    assert response.json()['results'][0]['content'] == "Find me."

def test_user_can_create_post(user_factory, api_client_factory):
    user = user_factory()
    client = api_client_factory(user=user)
    response = client.post('/api/posts/', {'content': 'A new post!'})
    assert response.status_code == status.HTTP_201_CREATED

def test_user_can_update_own_post(user_factory, api_client_factory):
    user = user_factory()
    post = StatusPost.objects.create(author=user, content="Original.")
    client = api_client_factory(user=user)
    response = client.patch(f'/api/posts/{post.id}/', {'content': 'Updated!'})
    assert response.status_code == status.HTTP_200_OK
    post.refresh_from_db()
    assert post.content == "Updated!"

def test_user_cannot_update_another_users_post(user_factory, api_client_factory):
    owner, attacker = user_factory(), user_factory()
    post = StatusPost.objects.create(author=owner, content="Original.")
    client = api_client_factory(user=attacker)
    response = client.patch(f'/api/posts/{post.id}/', {'content': 'Hacked!'})
    assert response.status_code in [403, 404]

def test_user_can_delete_own_post(user_factory, api_client_factory):
    user = user_factory()
    post = StatusPost.objects.create(author=user, content="Delete me.")
    client = api_client_factory(user=user)
    response = client.delete(f'/api/posts/{post.id}/')
    assert response.status_code == status.HTTP_204_NO_CONTENT

def test_user_cannot_delete_another_users_post(user_factory, api_client_factory):
    owner, attacker = user_factory(), user_factory()
    post = StatusPost.objects.create(author=owner, content="Safe.")
    client = api_client_factory(user=attacker)
    response = client.delete(f'/api/posts/{post.id}/')
    assert response.status_code in [403, 404]