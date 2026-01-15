# C:\Users\Vinay\Project\Loopline\tests\community\test_poll_interaction_api.py

import pytest
from rest_framework import status
from community.models import StatusPost, Poll, PollOption, User, PollVote
from tests.conftest import user_factory, api_client_factory, api_client

pytestmark = pytest.mark.django_db

@pytest.fixture
def poll_scenario(user_factory):
    """ Sets up a post with a poll, a creator, and a voter. """
    creator = user_factory()
    post = StatusPost.objects.create(author=creator)
    poll = Poll.objects.create(post=post, question="Best framework?")
    option1 = PollOption.objects.create(poll=poll, text="Vue")
    option2 = PollOption.objects.create(poll=poll, text="React")
    return {"creator": creator, "post": post, "poll": poll, "options": [option1, option2]}

def test_user_can_vote_on_poll(api_client_factory, poll_scenario, user_factory):
    """ Verifies an authenticated user can cast a vote on a poll option. """
    voter = user_factory()
    client = api_client_factory(user=voter)
    poll = poll_scenario['poll']
    option = poll_scenario['options'][0]
    
    # This URL now matches your urls.py file
    url = f"/api/polls/{poll.id}/options/{option.id}/vote/"
    response = client.post(url) # Your view doesn't need a payload

    assert response.status_code == status.HTTP_200_OK
    assert PollVote.objects.filter(user=voter, poll=poll, option=option).exists()

def test_user_can_change_their_vote(api_client_factory, poll_scenario, user_factory):
    """ Verifies a user can change their vote from one option to another. """
    voter = user_factory()
    client = api_client_factory(user=voter)
    poll = poll_scenario['poll']
    option1, option2 = poll_scenario['options']

    # Vote for option 1
    client.post(f"/api/polls/{poll.id}/options/{option1.id}/vote/")
    assert PollVote.objects.get(user=voter, poll=poll).option == option1

    # Change vote to option 2
    response = client.post(f"/api/polls/{poll.id}/options/{option2.id}/vote/")
    assert response.status_code == status.HTTP_200_OK
    assert PollVote.objects.get(user=voter, poll=poll).option == option2

def test_unauthenticated_user_cannot_vote(api_client, poll_scenario):
    """ Verifies an unauthenticated user gets a 401 Unauthorized error. """
    poll = poll_scenario['poll']
    option = poll_scenario['options'][0]
    url = f"/api/polls/{poll.id}/options/{option.id}/vote/"
    response = api_client.post(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# Add this function to the end of test_poll_interaction_api.py

def test_user_can_undo_their_vote_by_clicking_same_option(api_client_factory, poll_scenario, user_factory):
    """
    Verifies a user can withdraw their vote by sending a POST request for
    the same option they already voted for.
    """
    # Arrange
    voter = user_factory()
    client = api_client_factory(user=voter)
    poll = poll_scenario['poll']
    option1 = poll_scenario['options'][0]
    url = f"/api/polls/{poll.id}/options/{option1.id}/vote/"

    # Act 1: Cast the initial vote
    response1 = client.post(url)
    assert response1.status_code == status.HTTP_200_OK
    assert PollVote.objects.filter(user=voter, poll=poll).count() == 1

    # Act 2: Send the exact same request again to "undo" the vote
    response2 = client.post(url)
    assert response2.status_code == status.HTTP_200_OK

    # Assert: The vote should now be deleted
    assert PollVote.objects.filter(user=voter, poll=poll).count() == 0