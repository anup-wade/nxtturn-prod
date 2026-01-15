# community/utils.py

import re
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .models import Notification, Comment

User = get_user_model()

def process_mentions(actor, target_object, content_text):
    """
    Parses content text for @mentions and creates notifications.

    - actor: The user who wrote the content (the one doing the mentioning).
    - target_object: The instance of the post or comment where the mention occurred.
    - content_text: The raw text of the post/comment to be parsed.
    """
    if not content_text:
        return

    # Regex to find all words prefixed with @
    # Using a set ensures we only process each unique username once.
    mentioned_usernames = set(re.findall(r'@([\w.-]+)', content_text))

    if not mentioned_usernames:
        return

    # Find all valid User objects that match the mentioned usernames.
    # Exclude the actor so users don't get notifications for mentioning themselves.
    mentioned_users = User.objects.filter(username__in=mentioned_usernames).exclude(pk=actor.pk)

    notifications_to_create = []
    
    for user_to_notify in mentioned_users:
        # Determine the parent object author to avoid redundant notifications.
        # e.g., Don't notify if you're mentioned in a reply to your own post.
        parent_author = None
        if isinstance(target_object, Comment) and target_object.content_object:
            # If the mention is in a comment, the parent is the post/comment being replied to.
            parent_author = getattr(target_object.content_object, 'author', None)
        
        # If the user being notified is the author of the parent content, skip.
        # They will already get a "comment" or "reply" notification.
        if user_to_notify == parent_author:
            continue

        notification = Notification(
            recipient=user_to_notify,
            actor=actor,
            verb=f"mentioned you in a {target_object.__class__.__name__.lower()}",
            notification_type=Notification.MENTION,
            target=target_object
        )
        notifications_to_create.append(notification)

    if notifications_to_create:
        # bulk_create is efficient. ignore_conflicts prevents errors if a similar notification
        # was somehow created in the same transaction.
        Notification.objects.bulk_create(notifications_to_create, ignore_conflicts=True)