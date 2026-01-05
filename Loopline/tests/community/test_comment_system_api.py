# C:\Users\Vinay\Project\Loopline\tests\community\test_comment_system_api.py
import pytest
from rest_framework import status
from community.models import StatusPost, Comment
from tests.conftest import user_factory, api_client_factory, api_client

pytestmark = pytest.mark.django_db

@pytest.fixture
def post_scenario(user_factory):
    post_owner = user_factory()
    post = StatusPost.objects.create(author=post_owner, content="A post for testing.")
    return {"post": post}

def test_user_can_create_comment_on_post(user_factory, api_client_factory, post_scenario):
    user = user_factory()
    client = api_client_factory(user=user)
    url = f'/api/comments/statuspost/{post_scenario["post"].id}/'
    response = client.post(url, {'content': 'A new comment!'})
    assert response.status_code == status.HTTP_201_CREATED
    assert Comment.objects.count() == 1

def test_user_can_update_own_comment(user_factory, api_client_factory, post_scenario):
    user = user_factory()
    comment = Comment.objects.create(author=user, content_object=post_scenario["post"], content="Original.")
    client = api_client_factory(user=user)
    response = client.patch(f'/api/comments/{comment.id}/', {'content': 'Updated!'})
    assert response.status_code == status.HTTP_200_OK
    comment.refresh_from_db()
    assert comment.content == 'Updated!'

def test_user_cannot_update_another_users_comment(user_factory, api_client_factory, post_scenario):
    owner, attacker = user_factory(), user_factory()
    comment = Comment.objects.create(author=owner, content_object=post_scenario["post"], content="Original.")
    client = api_client_factory(user=attacker)
    response = client.patch(f'/api/comments/{comment.id}/', {'content': 'Hacked!'})
    assert response.status_code in [403, 404]

def test_user_can_delete_own_comment(user_factory, api_client_factory, post_scenario):
    user = user_factory()
    comment = Comment.objects.create(author=user, content_object=post_scenario["post"], content="Delete me.")
    client = api_client_factory(user=user)
    response = client.delete(f'/api/comments/{comment.id}/')
    assert response.status_code == status.HTTP_204_NO_CONTENT

def test_user_cannot_delete_another_users_comment(user_factory, api_client_factory, post_scenario):
    owner, attacker = user_factory(), user_factory()
    comment = Comment.objects.create(author=owner, content_object=post_scenario["post"], content="Safe.")
    client = api_client_factory(user=attacker)
    response = client.delete(f'/api/comments/{comment.id}/')
    assert response.status_code in [403, 404]

def test_user_can_create_reply_to_comment(user_factory, api_client_factory, post_scenario):
    user, replier = user_factory(), user_factory()
    parent = Comment.objects.create(author=user, content_object=post_scenario["post"], content="Parent.")
    client = api_client_factory(user=replier)
    url = f'/api/comments/statuspost/{post_scenario["post"].id}/'
    response = client.post(url, {'content': 'A reply!', 'parent': parent.id})
    assert response.status_code == status.HTTP_201_CREATED
    assert Comment.objects.count() == 2

def test_user_can_update_own_reply(user_factory, api_client_factory, post_scenario):
    user = user_factory()
    parent = Comment.objects.create(author=user, content_object=post_scenario["post"], content="Parent.")
    reply = Comment.objects.create(author=user, content_object=post_scenario["post"], content="Original.", parent=parent)
    client = api_client_factory(user=user)
    response = client.patch(f'/api/comments/{reply.id}/', {'content': 'Updated!'})
    assert response.status_code == status.HTTP_200_OK

def test_user_cannot_update_another_users_reply(user_factory, api_client_factory, post_scenario):
    owner, attacker = user_factory(), user_factory()
    parent = Comment.objects.create(author=owner, content_object=post_scenario["post"], content="Parent.")
    reply = Comment.objects.create(author=owner, content_object=post_scenario["post"], content="Original.", parent=parent)
    client = api_client_factory(user=attacker)
    response = client.patch(f'/api/comments/{reply.id}/', {'content': 'Hacked!'})
    assert response.status_code in [403, 404]

def test_user_can_delete_own_reply(user_factory, api_client_factory, post_scenario):
    user = user_factory()
    parent = Comment.objects.create(author=user, content_object=post_scenario["post"], content="Parent.")
    reply = Comment.objects.create(author=user, content_object=post_scenario["post"], content="Reply.", parent=parent)
    client = api_client_factory(user=user)
    response = client.delete(f'/api/comments/{reply.id}/')
    assert response.status_code == status.HTTP_204_NO_CONTENT

def test_user_cannot_delete_another_users_reply(user_factory, api_client_factory, post_scenario):
    owner, attacker = user_factory(), user_factory()
    parent = Comment.objects.create(author=owner, content_object=post_scenario["post"], content="Parent.")
    reply = Comment.objects.create(author=owner, content_object=post_scenario["post"], content="Reply.", parent=parent)
    client = api_client_factory(user=attacker)
    response = client.delete(f'/api/comments/{reply.id}/')
    assert response.status_code in [403, 404]