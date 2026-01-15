# C:\Users\Vinay\Project\Loopline\tests\community\test_report_api.py
import pytest
from rest_framework import status
from django.contrib.contenttypes.models import ContentType
from community.models import StatusPost, Comment, Report
from tests.conftest import user_factory, api_client_factory

pytestmark = pytest.mark.django_db

def test_user_can_report_post(user_factory, api_client_factory):
    owner, reporter = user_factory(), user_factory()
    post = StatusPost.objects.create(author=owner, content="Content to report.")
    client = api_client_factory(user=reporter)
    
    content_type = ContentType.objects.get_for_model(StatusPost)
    url = f'/api/content/{content_type.id}/{post.id}/report/'
    response = client.post(url, {'reason': 'SPAM'})
    
    assert response.status_code == status.HTTP_201_CREATED
    # CORRECTED ASSERTION
    assert Report.objects.filter(
        reporter=reporter, 
        content_type=content_type, 
        object_id=post.id
    ).exists()

def test_user_can_report_comment(user_factory, api_client_factory):
    owner, reporter = user_factory(), user_factory()
    post = StatusPost.objects.create(author=owner)
    comment = Comment.objects.create(author=owner, content_object=post, content="Comment to report.")
    client = api_client_factory(user=reporter)
    
    content_type = ContentType.objects.get_for_model(Comment)
    url = f'/api/content/{content_type.id}/{comment.id}/report/'
    response = client.post(url, {'reason': 'HATE_SPEECH'})
    
    assert response.status_code == status.HTTP_201_CREATED
    # CORRECTED ASSERTION
    assert Report.objects.filter(
        reporter=reporter, 
        content_type=content_type, 
        object_id=comment.id
    ).exists()

def test_user_can_report_reply(user_factory, api_client_factory):
    owner, reporter = user_factory(), user_factory()
    post = StatusPost.objects.create(author=owner)
    parent = Comment.objects.create(author=owner, content_object=post)
    reply = Comment.objects.create(author=owner, content_object=post, parent=parent, content="Reply to report.")
    client = api_client_factory(user=reporter)
    
    content_type = ContentType.objects.get_for_model(Comment)
    url = f'/api/content/{content_type.id}/{reply.id}/report/'
    response = client.post(url, {'reason': 'SPAM'})
    
    assert response.status_code == status.HTTP_201_CREATED
    # CORRECTED ASSERTION
    assert Report.objects.filter(
        reporter=reporter, 
        content_type=content_type, 
        object_id=reply.id
    ).exists()