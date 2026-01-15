import pytest
from django.contrib.auth import get_user_model
from community.models import StatusPost, Like, Notification, Comment, Follow, Group, GroupJoinRequest

@pytest.mark.django_db
def test_like_on_post_creates_one_notification():
    # ... (This is your first, working test)
    User = get_user_model()
    post_author = User.objects.create_user(username='post_author', password='password123')
    liking_user = User.objects.create_user(username='liking_user', password='password123')
    post = StatusPost.objects.create(author=post_author, content="This is a test post.")
    assert Notification.objects.count() == 0
    Like.objects.create(user=liking_user, content_object=post)
    assert Notification.objects.count() == 1
    notification = Notification.objects.first()
    assert notification.recipient == post_author
    assert notification.actor == liking_user
    assert notification.verb == 'liked your post'
    assert notification.target == post

@pytest.mark.django_db
def test_comment_on_post_creates_one_notification():
    # ... (This is your second, working test)
    User = get_user_model()
    post_author = User.objects.create_user(username='post_author_2', password='password123')
    commenting_user = User.objects.create_user(username='commenting_user', password='password123')
    post = StatusPost.objects.create(author=post_author, content="A post to be commented on.")
    assert Notification.objects.count() == 0
    Comment.objects.create(
        author=commenting_user,
        content_object=post,
        content="This is a test comment."
    )
    assert Notification.objects.count() == 1
    notification = Notification.objects.first()
    assert notification.recipient == post_author
    assert notification.actor == commenting_user
    assert notification.verb == 'commented on your post'
    assert isinstance(notification.target, Comment)
    assert notification.target.content == "This is a test comment."

@pytest.mark.django_db
def test_like_on_comment_creates_one_notification_for_comment_author():
    """
    Verifies that when a user likes a comment, exactly one notification
    is created for the author of that comment.
    """
    # 1. ARRANGE
    User = get_user_model()
    post_author = User.objects.create_user(username='post_author_3', password='password123')
    comment_author = User.objects.create_user(username='comment_author', password='password123')
    liking_user = User.objects.create_user(username='liking_user_3', password='password123')
    
    post = StatusPost.objects.create(author=post_author, content="A post for testing likes on comments.")
    comment = Comment.objects.create(
        author=comment_author, 
        content_object=post, 
        content="This comment will be liked."
    )
    
    assert Notification.objects.count() == 1
    initial_notification = Notification.objects.first()
    assert initial_notification.recipient == post_author

    # 2. ACT
    Like.objects.create(user=liking_user, content_object=comment)

    # 3. ASSERT
    assert Notification.objects.count() == 2
    
    # Note the corrected '-timestamp' here
    like_notification = Notification.objects.order_by('-timestamp', '-id').first()
    
    assert like_notification.recipient == comment_author
    assert like_notification.actor == liking_user
    assert "liked your comment" in like_notification.verb or "liked your reply" in like_notification.verb
    assert like_notification.target == comment

@pytest.mark.django_db
def test_like_on_own_post_does_not_create_notification():
    """
    Verifies that a notification is NOT created when a user
    likes their own post.
    """
    # 1. ARRANGE: We only need one user and one post.
    User = get_user_model()
    user = User.objects.create_user(username='self_liker', password='password123')
    post = StatusPost.objects.create(author=user, content="I will like my own post.")
    
    # We expect the database to be clean before the action.
    assert Notification.objects.count() == 0

    # 2. ACT: The user likes their own post.
    Like.objects.create(user=user, content_object=post)

    # 3. ASSERT: The number of notifications should still be zero.
    # This is the critical check for this test.
    assert Notification.objects.count() == 0

@pytest.mark.django_db
def test_reply_to_comment_creates_notification_for_parent_comment_author():
    """
    Verifies that replying to a comment creates a single notification
    for the author of the parent comment.
    """
    # 1. ARRANGE: We need a post author, a comment author, and a replier.
    User = get_user_model()
    post_author = User.objects.create_user(username='post_author_5', password='password123')
    comment_author = User.objects.create_user(username='comment_author_2', password='password123')
    replier = User.objects.create_user(username='replier', password='password123')

    post = StatusPost.objects.create(author=post_author, content="A post to test replies.")
    parent_comment = Comment.objects.create(
        author=comment_author, 
        content_object=post,
        content="This is the parent comment."
    )

    # Note: Creating the parent_comment creates 1 notification for the post_author.
    # We must account for this.
    assert Notification.objects.count() == 1

    # 2. ACT: The 'replier' creates a new comment, setting its 'parent'
    # to the comment made by 'comment_author'.
    Comment.objects.create(
        author=replier,
        content_object=post,
        content="This is a reply.",
        parent=parent_comment
    )

    # 3. ASSERT: The total notification count should now be 2.
    assert Notification.objects.count() == 2

    # Get the newest notification to ensure we're testing the reply.
    reply_notification = Notification.objects.order_by('-timestamp', '-id').first()

    # The recipient MUST be the author of the parent comment.
    assert reply_notification.recipient == comment_author
    
    assert reply_notification.actor == replier
    assert reply_notification.verb == "replied to your comment"

@pytest.mark.django_db
def test_like_on_reply_creates_notification_for_reply_author():
    """
    Verifies that liking a reply creates a notification for the author of
    the reply, with the correct verb.
    """
    # 1. ARRANGE: This is our most complex scenario, requiring four users.
    User = get_user_model()
    post_author = User.objects.create_user(username='post_author_6', password='password123')
    comment_author = User.objects.create_user(username='comment_author_3', password='password123')
    reply_author = User.objects.create_user(username='reply_author', password='password123')
    liking_user = User.objects.create_user(username='liking_user_4', password='password123')

    post = StatusPost.objects.create(author=post_author, content="A post for a deep thread.")
    parent_comment = Comment.objects.create(
        author=comment_author, 
        content_object=post,
        content="Parent comment."
    )
    reply_comment = Comment.objects.create(
        author=reply_author,
        content_object=post,
        content="A reply to the comment.",
        parent=parent_comment
    )

    # At this point, two notifications have been created:
    # 1. For the post_author when parent_comment was made.
    # 2. For the comment_author when reply_comment was made.
    assert Notification.objects.count() == 2

    # 2. ACT: The 'liking_user' likes the 'reply_comment'.
    Like.objects.create(user=liking_user, content_object=reply_comment)

    # 3. ASSERT: The total notification count should now be 3.
    assert Notification.objects.count() == 3

    # Get the newest notification to ensure we're testing the like on the reply.
    like_on_reply_notification = Notification.objects.order_by('-timestamp', '-id').first()

    # The recipient MUST be the author of the reply.
    assert like_on_reply_notification.recipient == reply_author
    
    assert like_on_reply_notification.actor == liking_user
    # Specifically check for the 'reply' verb.
    assert like_on_reply_notification.verb == "liked your reply"
    assert like_on_reply_notification.target == reply_comment

@pytest.mark.django_db
def test_mention_in_post_creates_notification():
    """
    Verifies that mentioning a user in a StatusPost creates a single
    notification for the user who was mentioned.
    """
    # 1. ARRANGE: We need a post author and a user to be mentioned.
    User = get_user_model()
    post_author = User.objects.create_user(username='post_author_7', password='password123')
    mentioned_user = User.objects.create_user(username='mentioned_user', password='password123')
    
    # Start with a clean slate.
    assert Notification.objects.count() == 0

    # 2. ACT: Create a StatusPost with content that includes an @-mention.
    # The 'post_save' signal on the StatusPost model should trigger our mention handler.
    post = StatusPost.objects.create(
        author=post_author, 
        content=f"This is a test post, a shout-out to @{mentioned_user.username}!"
    )

    # 3. ASSERT: A single, correct notification should now exist.
    assert Notification.objects.count() == 1
    
    notification = Notification.objects.first()
    
    # The recipient MUST be the user who was mentioned.
    assert notification.recipient == mentioned_user
    
    assert notification.actor == post_author
    assert notification.verb == "mentioned you in a post"
    # For a mention in a post, the target should be the post itself.
    assert notification.target == post

@pytest.mark.django_db
def test_mention_in_comment_creates_notification():
    """
    Verifies that mentioning a user in a comment creates a notification
    for the mentioned user.
    """
    # 1. ARRANGE: We need a post author, comment author, and mentioned user.
    User = get_user_model()
    post_author = User.objects.create_user(username='post_author_8', password='password123')
    comment_author = User.objects.create_user(username='comment_author_4', password='password123')
    mentioned_user = User.objects.create_user(username='mentioned_user_2', password='password123')

    post = StatusPost.objects.create(author=post_author, content="A post for testing mentions in comments.")

    # Note: Creating the comment below will also trigger the standard
    # "comment on your post" notification for the post_author. We must account for this.
    assert Notification.objects.count() == 0

    # 2. ACT: Create a Comment that contains an @-mention.
    Comment.objects.create(
        author=comment_author,
        content_object=post,
        content=f"Great point! Hey @{mentioned_user.username}, what do you think?"
    )

    # 3. ASSERT: Two notifications should now exist.
    # 1. The standard "comment on your post" notification for post_author.
    # 2. The "mentioned you in a comment" notification for mentioned_user.
    assert Notification.objects.count() == 2

    # Find the specific mention notification to test its details.
    mention_notification = Notification.objects.get(recipient=mentioned_user)

    assert mention_notification.actor == comment_author
    assert "mentioned you in a comment" in mention_notification.verb
    # The target for a mention in a comment should be the PARENT POST,
    # so the user can get context for the comment.
    assert mention_notification.target == post

@pytest.mark.django_db
def test_mention_in_reply_creates_notification():
    """
    Verifies that mentioning a user in a reply to a comment creates a
    notification for the mentioned user with the correct 'reply' verb.
    """
    # 1. ARRANGE: We need four users to make this test unambiguous.
    User = get_user_model()
    post_author = User.objects.create_user(username='post_author_9', password='password123')
    comment_author = User.objects.create_user(username='comment_author_5', password='password123')
    reply_author = User.objects.create_user(username='reply_author_2', password='password123')
    mentioned_user = User.objects.create_user(username='mentioned_user_3', password='password123')

    post = StatusPost.objects.create(author=post_author, content="A post for testing mentions in replies.")
    parent_comment = Comment.objects.create(author=comment_author, content_object=post, content="The first comment.")

    # At this point, 1 notification exists for the post_author.
    assert Notification.objects.count() == 1

    # 2. ACT: The reply_author replies to the parent_comment and mentions a third user.
    Comment.objects.create(
        author=reply_author,
        content_object=post,
        content=f"I agree! What do you think, @{mentioned_user.username}?",
        parent=parent_comment
    )

    # 3. ASSERT: Three notifications should now exist in total.
    # 1. To post_author for the parent_comment. (From Arrange)
    # 2. To comment_author for the reply. (From Act)
    # 3. To mentioned_user for the mention. (From Act)
    assert Notification.objects.count() == 3

    # Isolate the specific mention notification for detailed checks.
    mention_notification = Notification.objects.get(
        recipient=mentioned_user,
        verb__contains="mentioned" # A robust way to find it
    )

    assert mention_notification.actor == reply_author
    # This is the critical check for this test case.
    assert mention_notification.verb == "mentioned you in a reply"
    assert mention_notification.target == post

@pytest.mark.django_db
def test_like_on_own_comment_does_not_create_notification():
    """
    Verifies that a notification is NOT created when a user
    likes their own comment.
    """
    # 1. ARRANGE: We need a post author and a user who will comment and like.
    User = get_user_model()
    post_author = User.objects.create_user(username='post_author_10', password='password123')
    # This user will perform all actions.
    active_user = User.objects.create_user(username='self_comment_liker', password='password123')

    post = StatusPost.objects.create(author=post_author, content="A post for self-like testing.")
    
    # The active_user creates a comment. This will generate one notification
    # for the post_author, which we must account for.
    own_comment = Comment.objects.create(
        author=active_user,
        content_object=post,
        content="I am about to like this comment myself."
    )
    
    assert Notification.objects.count() == 1

    # 2. ACT: The active_user likes their own comment.
    Like.objects.create(user=active_user, content_object=own_comment)

    # 3. ASSERT: The number of notifications should NOT have increased.
    # It should still be 1 (the original notification to the post_author).
    assert Notification.objects.count() == 1

@pytest.mark.django_db
def test_reply_to_own_comment_does_not_create_notification():
    """
    Verifies that a notification is NOT created when a user replies
    to their own comment.
    """
    # 1. ARRANGE: We need a post author and an active user.
    User = get_user_model()
    post_author = User.objects.create_user(username='post_author_11', password='password123')
    active_user = User.objects.create_user(username='self_replier', password='password123')

    post = StatusPost.objects.create(author=post_author, content="A post for self-reply testing.")
    
    # The active_user creates the parent comment. This generates one
    # notification for the post_author.
    parent_comment = Comment.objects.create(
        author=active_user,
        content_object=post,
        content="This is my first comment."
    )
    
    assert Notification.objects.count() == 1

    # 2. ACT: The active_user replies to their own parent comment.
    Comment.objects.create(
        author=active_user,
        content_object=post,
        content="This is me replying to myself.",
        parent=parent_comment
    )

    # 3. ASSERT: The number of notifications should NOT have increased.
    # The self-reply should be ignored by the notification system.
    assert Notification.objects.count() == 1

@pytest.mark.django_db
def test_like_on_own_reply_does_not_create_notification():
    """
    Verifies that a notification is NOT created when a user
    likes their own reply.
    """
    # 1. ARRANGE: We need a post author, a comment author, and our active user.
    User = get_user_model()
    post_author = User.objects.create_user(username='post_author_12', password='password123')
    comment_author = User.objects.create_user(username='comment_author_6', password='password123')
    active_user = User.objects.create_user(username='self_reply_liker', password='password123')

    post = StatusPost.objects.create(author=post_author, content="A post for self-reply-like testing.")
    parent_comment = Comment.objects.create(
        author=comment_author,
        content_object=post,
        content="A parent comment."
    )
    # The active_user creates a reply to the parent comment.
    own_reply = Comment.objects.create(
        author=active_user,
        content_object=post,
        content="This is my own reply.",
        parent=parent_comment
    )

    # At this point, two notifications exist:
    # 1. For post_author when parent_comment was made.
    # 2. For comment_author when own_reply was made.
    assert Notification.objects.count() == 2

    # 2. ACT: The active_user likes their own reply.
    Like.objects.create(user=active_user, content_object=own_reply)

    # 3. ASSERT: The number of notifications should NOT have increased.
    assert Notification.objects.count() == 2

@pytest.mark.django_db
def test_follow_creates_notification():
    """
    Verifies that when a user follows another user, a single notification
    is created for the user who was followed.
    """
    # 1. ARRANGE: We need two users for this action.
    User = get_user_model()
    followed_user = User.objects.create_user(username='followed_user', password='password123')
    follower = User.objects.create_user(username='follower', password='password123')

    # Start with a clean database.
    assert Notification.objects.count() == 0

    # 2. ACT: The 'follower' follows the 'followed_user'.
    # This action should trigger the post_save signal for the Follow model.
    Follow.objects.create(follower=follower, following=followed_user)

    # 3. ASSERT: A single, correct notification should now exist.
    assert Notification.objects.count() == 1

    notification = Notification.objects.first()

    assert notification.recipient == followed_user
    assert notification.actor == follower
    assert notification.verb == "started following you"

@pytest.mark.django_db
def test_self_mention_in_post_does_not_create_notification():
    """
    Verifies that a notification is NOT created when a user
    mentions themselves in a post.
    """
    # 1. ARRANGE: We only need one user for this test.
    User = get_user_model()
    active_user = User.objects.create_user(username='self_mentioner', password='password123')

    # Start with a clean database.
    assert Notification.objects.count() == 0

    # 2. ACT: The user creates a post and mentions themselves.
    StatusPost.objects.create(
        author=active_user,
        content=f"This is a note to myself, @{active_user.username}."
    )

    # 3. ASSERT: The number of notifications should still be zero.
    assert Notification.objects.count() == 0

@pytest.mark.django_db
def test_self_mention_in_comment_does_not_create_notification():
    """
    Verifies that a notification is NOT created when a user
    mentions themselves in a comment.
    """
    # 1. ARRANGE
    User = get_user_model()
    post_author = User.objects.create_user(username='post_author_13', password='password123')
    active_user = User.objects.create_user(username='self_mentioner_2', password='password123')

    post = StatusPost.objects.create(author=post_author, content="A post for self-mention testing in comments.")

    # 2. ACT: The active_user comments on the post and mentions themselves.
    # This action will create ONE notification for the post_author.
    # The self-mention notification should be suppressed.
    Comment.objects.create(
        author=active_user,
        content_object=post,
        content=f"A reminder for @{active_user.username} to check this later."
    )

    # 3. ASSERT: Only one notification (for the post author) should exist.
    assert Notification.objects.count() == 1
    
    # Verify that the single existing notification is indeed for the post author,
    # and not an incorrect self-mention notification.
    notification = Notification.objects.first()
    assert notification.recipient == post_author

@pytest.mark.django_db
def test_self_mention_in_reply_does_not_create_notification():
    """
    Verifies that a notification is NOT created when a user
    mentions themselves in a reply.
    """
    # 1. ARRANGE
    User = get_user_model()
    post_author = User.objects.create_user(username='post_author_14', password='password123')
    comment_author = User.objects.create_user(username='comment_author_7', password='password123')
    active_user = User.objects.create_user(username='self_mentioner_3', password='password123')

    post = StatusPost.objects.create(author=post_author, content="A post for self-mention reply testing.")
    parent_comment = Comment.objects.create(
        author=comment_author,
        content_object=post,
        content="A parent comment for the reply."
    )
    # This setup creates 1 notification (to the post author).

    # 2. ACT: The active_user replies to the comment_author and mentions themselves.
    # This should create ONE notification for the comment_author.
    # The self-mention notification should be suppressed.
    Comment.objects.create(
        author=active_user,
        content_object=post,
        content=f"Good point. Note to @{active_user.username}: follow up on this.",
        parent=parent_comment
    )

    # 3. ASSERT: Exactly two notifications should exist in total.
    # 1. To post_author for parent_comment.
    # 2. To comment_author for the new reply.
    assert Notification.objects.count() == 2

    # Double-check that no notification was sent to the active_user.
    # This makes the test even more explicit and robust.
    assert not Notification.objects.filter(recipient=active_user).exists()

# (at the end of test_signals.py)

@pytest.mark.django_db
def test_notification_created_on_private_group_join_request(user_factory):
    """
    Tests that a notification is sent to the group owner when a user
    requests to join their private group.
    """
    # --- Arrange ---
    group_owner = user_factory()
    requester = user_factory()
    private_group = Group.objects.create(
        creator=group_owner, 
        name="Exclusive Signal Testers", 
        privacy_level='private'
    )
    
    assert Notification.objects.count() == 0

    # --- Act ---
    join_request = GroupJoinRequest.objects.create(user=requester, group=private_group)

    # --- Assert ---
    assert Notification.objects.count() == 1
    
    notification = Notification.objects.first()
    
    assert notification.recipient == group_owner
    assert notification.actor == requester
    assert notification.verb == "sent a request to join"
    assert notification.target == private_group
    assert notification.action_object == join_request

