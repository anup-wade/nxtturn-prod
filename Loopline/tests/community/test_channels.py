# C:\Users\Vinay\Project\Loopline\community\test_channels.py
# --- FIXED to match updated consumer logic ---

import pytest
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
import asyncio


from community.models import StatusPost, Follow, Like, Comment, Group, GroupJoinRequest, Notification
from config.asgi import application

pytestmark = pytest.mark.django_db(transaction=True)

# --- Async Helper Functions (Unchanged) ---

@database_sync_to_async
def create_user(username, password='password123'):
    User = get_user_model()
    return User.objects.create_user(username=username, password=password)

@database_sync_to_async
def create_follow(follower, following):
    return Follow.objects.create(follower=follower, following=following)

@database_sync_to_async
def create_post(author, content):
    return StatusPost.objects.create(author=author, content=content)

@database_sync_to_async
def get_auth_token(user):
    token, _ = Token.objects.get_or_create(user=user)
    return token.key

@database_sync_to_async
def create_like(user, content_object):
    return Like.objects.create(user=user, content_object=content_object)

@database_sync_to_async
def create_comment(author, content_object, content, parent=None):
    return Comment.objects.create(
        author=author,
        content_object=content_object,
        content=content,
        parent=parent
    )

@database_sync_to_async
def create_group(creator, name, privacy_level='public'):
    return Group.objects.create(creator=creator, name=name, privacy_level=privacy_level)

# ===============================================================
# POSITIVE PATH REAL-TIME TESTS
# ===============================================================

@pytest.mark.asyncio
async def test_new_post_sends_live_signal_to_follower():
    author = await create_user('live_author')
    follower = await create_user('live_follower')
    await create_follow(follower=follower, following=author)

    follower_token = await get_auth_token(follower)
    connection_url = f"/ws/activity/?token={follower_token}"
    
    communicator = WebsocketCommunicator(application, connection_url)
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection failed."

    post = await create_post(author=author, content="A live post!")

    # [FIX] Consumer now sends the message directly, no wrapper.
    response = await communicator.receive_json_from(timeout=1)
    
    # [FIX] Assert the new, direct message type.
    assert response['type'] == 'new_post'
    assert response['payload']['id'] == post.id

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_post_deleted_sends_signal_to_follower():
    """
    CRITICAL: Verifies that when a post is deleted, a 'post_deleted' signal
    is sent to the author's followers, ensuring real-time UI consistency for everyone.
    """
    author = await create_user('author_with_follower_rt')
    follower = await create_user('follower_of_deleter_rt')
    await create_follow(follower=follower, following=author)
    
    post_to_delete = await create_post(author=author, content="This post will be deleted from all feeds.")

    # --- THIS IS THE FIX ---
    # Save the ID before deleting the object, because the ID becomes None after deletion.
    post_id_before_delete = post_to_delete.id
    # --- END OF FIX ---

    # Connect to the WebSocket as the FOLLOWER
    follower_token = await get_auth_token(follower)
    connection_url = f"/ws/activity/?token={follower_token}"
    
    communicator = WebsocketCommunicator(application, connection_url)
    connected, _ = await communicator.connect()
    assert connected, "Follower WebSocket connection failed."

    # The author deletes the post
    await database_sync_to_async(post_to_delete.delete)()

    # ASSERT: The follower MUST receive the deletion signal.
    response = await communicator.receive_json_from(timeout=2)
    
    assert response['type'] == 'post_deleted'
    # Compare against the ID we saved before the deletion
    assert response['payload']['post_id'] == post_id_before_delete
    
    await communicator.disconnect()

@pytest.mark.asyncio
async def test_like_on_post_sends_realtime_notification():
    author = await create_user('notification_recipient')
    liker = await create_user('notification_actor')
    post = await create_post(author=author, content="A post to be liked.")

    author_token = await get_auth_token(author)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={author_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection for author failed."

    await create_like(user=liker, content_object=post)

    # [FIX] Consumer now sends the message directly, no wrapper.
    response = await communicator.receive_json_from(timeout=1)

    # [FIX] Assert the new, direct message type.
    assert response['type'] == 'new_notification'
    
    payload = response['payload']
    assert payload['verb'] == 'liked your post'
    assert payload['actor']['username'] == liker.username

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_comment_on_post_sends_realtime_notification():
    author = await create_user('post_author_rt')
    commenter = await create_user('commenter_rt')
    post = await create_post(author=author, content="A post to be commented on.")

    author_token = await get_auth_token(author)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={author_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection for author failed."

    await create_comment(author=commenter, content_object=post, content="A real-time comment!")

    # [FIX] Consumer now sends the message directly, no wrapper.
    response = await communicator.receive_json_from(timeout=1)
    
    # [FIX] Assert the new, direct message type.
    assert response['type'] == 'new_notification'
    payload = response['payload']
    
    assert payload['verb'] == 'commented on your post'
    assert payload['actor']['username'] == commenter.username
    assert payload['context_snippet'] == '"A real-time comment!"'

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_mention_in_post_sends_realtime_notification():
    author = await create_user('mentioner_rt')
    mentioned_user = await create_user('mentioned_rt')

    mentioned_user_token = await get_auth_token(mentioned_user)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={mentioned_user_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection for mentioned user failed."

    await create_post(
        author=author,
        content=f"This is a real-time mention for @{mentioned_user.username}!"
    )

    # [FIX] Consumer now sends the message directly, no wrapper.
    response = await communicator.receive_json_from(timeout=1)
    
    # [FIX] Assert the new, direct message type.
    assert response['type'] == 'new_notification'
    payload = response['payload']
    
    assert payload['verb'] == 'mentioned you in a post'
    assert payload['actor']['username'] == author.username
    assert f"@{mentioned_user.username}" in payload['context_snippet']

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_follow_sends_realtime_notification():
    followed_user = await create_user('followed_rt')
    follower = await create_user('follower_rt')

    followed_user_token = await get_auth_token(followed_user)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={followed_user_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection for followed user failed."

    await create_follow(follower=follower, following=followed_user)

    # [FIX] Consumer now sends the message directly, no wrapper.
    response = await communicator.receive_json_from(timeout=1)
    
    # [FIX] Assert the new, direct message type.
    assert response['type'] == 'new_notification'
    payload = response['payload']
    
    assert payload['verb'] == 'started following you'
    assert payload['actor']['username'] == follower.username

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_like_on_comment_sends_realtime_notification():
    comment_author = await create_user('comment_author_rt')
    liker = await create_user('liker_rt')
    post_author = await create_user('post_author_for_comment_like_rt')
    post = await create_post(author=post_author, content="A post.")
    comment = await create_comment(
        author=comment_author, 
        content_object=post, 
        content="A comment to be liked in real-time."
    )

    comment_author_token = await get_auth_token(comment_author)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={comment_author_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection failed."

    await create_like(user=liker, content_object=comment)

    # [FIX] Consumer now sends the message directly, no wrapper.
    response = await communicator.receive_json_from(timeout=1)
    
    # [FIX] Assert the new, direct message type.
    assert response['type'] == 'new_notification'
    payload = response['payload']
    
    assert payload['verb'] == 'liked your comment'
    assert payload['actor']['username'] == liker.username

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_reply_to_comment_sends_realtime_notification():
    comment_author = await create_user('parent_comment_author_rt')
    replier = await create_user('replier_rt')
    post_author = await create_user('post_author_for_reply_rt')
    post = await create_post(author=post_author, content="A post.")
    parent_comment = await create_comment(
        author=comment_author, 
        content_object=post, 
        content="The parent comment for the real-time reply."
    )

    comment_author_token = await get_auth_token(comment_author)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={comment_author_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection failed."

    await create_comment(
        author=replier, 
        content_object=post, 
        content="This is a real-time reply.",
        parent=parent_comment
    )

    # [FIX] Consumer now sends the message directly, no wrapper.
    response = await communicator.receive_json_from(timeout=1)
    
    # [FIX] Assert the new, direct message type.
    assert response['type'] == 'new_notification'
    payload = response['payload']
    
    assert payload['verb'] == 'replied to your comment'
    assert payload['actor']['username'] == replier.username

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_mention_in_comment_sends_realtime_notification():
    comment_author = await create_user('comment_mentioner_rt')
    mentioned_user = await create_user('mentioned_in_comment_rt')
    post_author = await create_user('post_author_for_mention_rt')
    post = await create_post(author=post_author, content="A post.")

    mentioned_user_token = await get_auth_token(mentioned_user)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={mentioned_user_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection failed."

    await create_comment(
        author=comment_author,
        content_object=post,
        content=f"This is a real-time mention in a comment for @{mentioned_user.username}!"
    )

    # [FIX] Consumer now sends the message directly, no wrapper.
    response = await communicator.receive_json_from(timeout=1)
    
    # [FIX] Assert the new, direct message type.
    assert response['type'] == 'new_notification'
    payload = response['payload']
    
    assert 'mentioned you in a comment' in payload['verb']
    assert payload['actor']['username'] == comment_author.username

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_realtime_notification_on_group_join_request(user_factory, channel_layer):
    group_owner = await database_sync_to_async(user_factory)(username_prefix='owner')
    requester = await database_sync_to_async(user_factory)(username_prefix='requester')
    
    private_group = await create_group(
        creator=group_owner, 
        name="Realtime Group Test", 
        privacy_level='private'
    )

    await database_sync_to_async(Notification.objects.all().delete)()
    assert await database_sync_to_async(Notification.objects.count)() == 0

    owner_token = await get_auth_token(group_owner)
    connection_url = f"/ws/activity/?token={owner_token}"
    
    communicator = WebsocketCommunicator(application, connection_url)
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection for group owner failed."

    join_request = await database_sync_to_async(GroupJoinRequest.objects.create)(
        user=requester, 
        group=private_group
    )

    assert await database_sync_to_async(Notification.objects.count)() == 1
    db_notification = await database_sync_to_async(Notification.objects.first)()
    assert (await database_sync_to_async(lambda: db_notification.recipient_id)()) == group_owner.id
    assert db_notification.notification_type == Notification.GROUP_JOIN_REQUEST

    # [FIX] Consumer now sends the message directly, no wrapper.
    response = await communicator.receive_json_from(timeout=1)

    # [FIX] Assert the new, direct message type.
    assert response['type'] == 'new_notification'
    
    payload = response['payload']
    assert payload['actor']['username'] == requester.username
    assert payload['verb'] == "sent a request to join"
    assert payload['notification_type'] == 'group_join_request'
    assert payload['target']['display_text'] == private_group.name
    assert payload['target']['slug'] == private_group.slug
    assert payload['action_object']['id'] == join_request.id

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_realtime_notification_on_group_join_approval():
    group_owner = await create_user(username='approver_rt')
    requester = await create_user(username='requester_rt')
    
    private_group = await create_group(
        creator=group_owner, 
        name="Realtime Approval Group", 
        privacy_level='private'
    )
    
    join_request = await database_sync_to_async(GroupJoinRequest.objects.create)(
        user=requester, 
        group=private_group
    )

    requester_token = await get_auth_token(requester)
    connection_url = f"/ws/activity/?token={requester_token}"
    
    communicator = WebsocketCommunicator(application, connection_url)
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection for requester failed."

    await database_sync_to_async(private_group.members.add)(requester)
    
    join_request.status = 'approved'
    await database_sync_to_async(join_request.save)()
    
    await database_sync_to_async(Notification.objects.create)(
        recipient=requester,
        actor=group_owner,
        verb=f"approved your request to join the group",
        notification_type=Notification.GROUP_JOIN_APPROVED,
        target=private_group
    )

    # [FIX] Consumer now sends the message directly, no wrapper.
    response = await communicator.receive_json_from(timeout=1)
    
    # [FIX] Assert the new, direct message type.
    assert response['type'] == 'new_notification'
    
    payload = response['payload']
    assert payload['actor']['username'] == group_owner.username
    assert payload['notification_type'] == 'group_join_approved'
    assert payload['target']['display_text'] == private_group.name

    await communicator.disconnect()

# ===============================================================
# NEGATIVE PATH REAL-TIME TESTS (Unchanged)
# ===============================================================

@pytest.mark.asyncio
async def test_like_on_own_post_does_not_send_realtime_notification():
    user = await create_user('self_liker_rt')
    post = await create_post(author=user, content="A post to be self-liked.")
    user_token = await get_auth_token(user)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={user_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection failed."

    await create_like(user=user, content_object=post)
    await communicator.receive_nothing()

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_reply_to_own_comment_does_not_send_realtime_notification():
    user = await create_user('self_replier_rt')
    post = await create_post(author=user, content="A post for self-reply testing.")
    parent_comment = await create_comment(author=user, content_object=post, content="My parent comment.")
    user_token = await get_auth_token(user)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={user_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection failed."

    await create_comment(author=user, content_object=post, content="My self-reply.", parent=parent_comment)
    await communicator.receive_nothing()

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_self_mention_in_post_does_not_send_realtime_notification():
    user = await create_user('self_mentioner_rt')
    user_token = await get_auth_token(user)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={user_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection failed."

    await create_post(author=user, content=f"A note for @{user.username}")
    await communicator.receive_nothing()

    await communicator.disconnect()