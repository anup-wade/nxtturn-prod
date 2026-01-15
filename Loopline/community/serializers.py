import json
from rest_framework import serializers, validators
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Count
from .utils import process_mentions
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import PasswordResetConfirmSerializer
from allauth.account.forms import SetPasswordForm as AllAuthSetPasswordForm

from dj_rest_auth.serializers import LoginSerializer
from allauth.account.models import EmailAddress
from rest_framework import serializers


# Updated model imports to include PostMedia
from .models import (
    UserProfile,
    Follow,
    StatusPost,
    PostMedia,
    Group,
    Comment,
    Like,
    Conversation,
    Message,
    Notification,
    Poll,
    PollOption,
    Report,
    GroupJoinRequest,
    GroupBlock,
    ConnectionRequest,
    Skill,
    Education,
    Experience,
    SocialLink,
)

User = get_user_model()


class PostMediaSerializer(serializers.ModelSerializer):
    # Change the 'file_url' to be a simple URLField that gets the URL directly.
    # DRF and Cloudinary will handle generating the full URL automatically.
    file_url = serializers.URLField(source="file.url", read_only=True)

    class Meta:
        model = PostMedia
        # We only need to expose the final URL, not the raw file object.
        fields = ["id", "media_type", "file_url"]


class PollOptionSerializer(serializers.ModelSerializer):
    vote_count = serializers.SerializerMethodField()

    class Meta:
        model = PollOption
        fields = ["id", "text", "vote_count"]

    def get_vote_count(self, obj):
        # The 'votes' related_name on PollVote is pre-counted in the PollSerializer context
        return self.context.get("vote_counts", {}).get(obj.id, 0)


class PollSerializer(serializers.ModelSerializer):
    options = PollOptionSerializer(many=True, read_only=True)
    total_votes = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()

    class Meta:
        model = Poll
        fields = ["id", "question", "options", "total_votes", "user_vote"]

    # --- THIS IS THE CORRECTED METHOD ---
    def get_total_votes(self, obj):
        """
        Calculates the total votes by summing the pre-calculated counts
        from the context, which was populated by to_representation.
        This avoids a redundant database query.
        """
        vote_counts_dict = self.context.get("vote_counts", {})
        return sum(vote_counts_dict.values())

    def get_user_vote(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        vote = obj.votes.filter(user=request.user).first()
        return vote.option_id if vote else None

    def to_representation(self, instance):
        """
        Optimize vote counting to avoid N+1 queries.
        We count all votes for all options in one go.
        """
        vote_counts = {
            item["id"]: item["count"]
            for item in instance.options.annotate(count=Count("votes")).values(
                "id", "count"
            )
        }

        self.context["vote_counts"] = vote_counts
        return super().to_representation(instance)


# In community/serializers.py

# community/serializers.py


class UserSerializer(serializers.ModelSerializer):
    picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "picture"]

    def get_picture(self, obj):
        """
        Returns the absolute URL for the user's profile picture.
        """
        request = self.context.get("request")
        if not request:
            return None

        try:
            if (
                hasattr(obj, "profile")
                and obj.profile.picture
                and hasattr(obj.profile.picture, "url")
            ):
                return request.build_absolute_uri(obj.profile.picture.url)
        except UserProfile.DoesNotExist:
            pass

        return None


class CustomRegisterSerializer(RegisterSerializer):
    # This field will be used to explicitly validate email uniqueness.
    email = serializers.EmailField(
        required=True,
        # This validator checks if an object with this email already exists in the User model.
        validators=[validators.UniqueValidator(queryset=User.objects.all())],
    )

    def custom_signup(self, request, user):
        """
        You can add custom logic here that runs after a user is created.
        For now, we just pass.
        """
        pass


class ConnectionRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a ConnectionRequest.
    Its only job is to validate that the 'receiver' exists and is not the sender.
    """

    class Meta:
        model = ConnectionRequest
        fields = ["id", "receiver"]  # Only 'receiver' is needed for creation.

    def validate_receiver(self, value):
        sender = self.context["request"].user
        if sender == value:
            raise serializers.ValidationError(
                "You cannot send a connection request to yourself."
            )
        return value


class ConnectionRequestListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing received connection requests.
    Includes nested data for the sender.
    """

    # We want to show the full details of the person who sent the request,
    # so we use our existing UserSerializer here.
    sender = UserSerializer(read_only=True)

    class Meta:
        model = ConnectionRequest
        # We display the sender's info, which is more useful than just their ID.
        fields = ["id", "sender", "status", "created_at"]


class ReportSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and viewing content reports.
    """

    # Display the reporter's username for read operations, but don't require it for write.
    reporter = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Report
        # These are the fields we will show in the API response
        fields = ["id", "reporter", "reason", "details", "status", "created_at"]
        # These fields are set by the server, not the client
        read_only_fields = ["id", "reporter", "status", "created_at"]

    def validate(self, data):
        """
        Custom validation to check for duplicate reports and existence of the content object.
        """
        request = self.context.get("request")
        view = self.context.get("view")

        ct_id = view.kwargs.get("ct_id")
        obj_id = view.kwargs.get("obj_id")

        # 1. Validate that the content object actually exists
        try:
            content_type = ContentType.objects.get_for_id(ct_id)
            model_class = content_type.model_class()
            # We just need to check if it exists, no need to fetch the whole object here
            if not model_class.objects.filter(pk=obj_id).exists():
                raise serializers.ValidationError(
                    "The content you are trying to report does not exist."
                )
        except ContentType.DoesNotExist:
            raise serializers.ValidationError("Invalid content type for report.")

        # 2. Validate that the user hasn't already reported this exact item
        if Report.objects.filter(
            reporter=request.user, content_type=content_type, object_id=obj_id
        ).exists():
            raise serializers.ValidationError(
                {"detail": "You have already reported this content."}
            )

        # 3. If reason is 'OTHER', details must be provided
        if data.get("reason") == "OTHER" and not data.get("details", "").strip():
            raise serializers.ValidationError(
                {
                    "details": "Details are required when selecting 'Other' as the reason."
                }
            )

        return data

    def create(self, validated_data):
        """
        Create a new Report instance, setting the reporter and content object
        from the request context and URL kwargs.
        """
        request = self.context.get("request")
        view = self.context.get("view")

        ct_id = view.kwargs.get("ct_id")
        obj_id = view.kwargs.get("obj_id")

        content_type = ContentType.objects.get_for_id(ct_id)

        # Set the server-side fields
        validated_data["reporter"] = request.user
        validated_data["content_type"] = content_type
        validated_data["object_id"] = obj_id

        return Report.objects.create(**validated_data)


class GenericRelatedObjectSerializer(serializers.Serializer):
    type = serializers.CharField(read_only=True, source="_meta.model_name")
    id = serializers.IntegerField(read_only=True, source="pk")
    display_text = serializers.CharField(read_only=True, source="__str__")

    # This is for linking back to parent posts from comments/replies.
    object_id = serializers.SerializerMethodField()

    # --- THIS IS THE NEW FIELD FOR CREATING URLS ON THE FRONTEND ---
    slug = serializers.CharField(
        read_only=True, default=None
    )  # Corrected: Removed redundant source='slug'

    def get_object_id(self, obj):
        """
        Return the 'object_id' if the object has it (like a Comment),
        otherwise return the object's own ID as a fallback.
        """
        if hasattr(obj, "object_id"):
            return obj.object_id
        return obj.pk


class NotificationSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)
    target = GenericRelatedObjectSerializer(read_only=True, allow_null=True)
    action_object = GenericRelatedObjectSerializer(read_only=True, allow_null=True)

    # --- 1. ADD THIS NEW FIELD ---
    context_snippet = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        # --- 2. ADD 'context_snippet' TO THE FIELDS LIST ---
        fields = [
            "id",
            "actor",
            "verb",
            "notification_type",
            "target",
            "action_object",
            "timestamp",
            "is_read",
            "context_snippet",
        ]
        read_only_fields = fields

    # --- 3. ADD THIS ENTIRE NEW METHOD INSIDE THE CLASS ---
    # --- FINAL, PERFECTED REPLACEMENT ---
    def get_context_snippet(self, obj: Notification) -> str | None:
        """
        Generates a short preview of the content related to the notification.
        This version is the definitive one, handling all cases correctly.
        """
        source_object = None

        # For comments, replies, AND mentions, the most relevant new content
        # is the comment/reply/post where the action happened. This is always the action_object.
        if obj.notification_type in ["comment", "reply", "mention"]:
            source_object = obj.action_object

        # For likes, the content we want to show is on the object that was liked, which is the target.
        elif obj.notification_type == "like":
            source_object = obj.target

        # Now that we have the correct source_object, extract its content.
        if (
            source_object
            and hasattr(source_object, "content")
            and source_object.content
        ):
            content = str(source_object.content)
            truncate_at = 75
            if len(content) > truncate_at:
                return f'"{content[:truncate_at]}..."'
            return f'"{content}"'

        # Return None for 'follow' or if no content is found.
        return None


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name"]


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = [
            "id",
            "institution",
            "degree",
            "field_of_study",
            "university",
            "board",
            "start_date",
            "end_date",
            "description",
            "location",
            "achievements",
        ]


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = [
            "id",
            "title",
            "company",
            "location",
            "start_date",
            "end_date",
            "description",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        """
        Check that start_date is before end_date.
        """
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                {"end_date": "End date cannot be before start date."}
            )
        return data


class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        # We only need to expose these three fields to the API
        fields = ["id", "link_type", "url"]
        # Make the id read-only, as it's assigned by the database
        read_only_fields = ["id"]


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    skills = SkillSerializer(many=True, read_only=True, source="user.skills")
    education = EducationSerializer(
        many=True, read_only=True, source="education_history"
    )
    experience = ExperienceSerializer(
        many=True, read_only=True, source="experience_history"
    )

    # --- THIS IS THE FIX ---
    # Explicitly define the serializer for the 'social_links' relationship
    social_links = SocialLinkSerializer(many=True, read_only=True)
    # --- END OF FIX ---

    relationship_status = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "user",
            "display_name",
            "headline",
            "bio",
            # New Location Fields
            "location_city",
            "location_administrative_area",
            "location_country",
            "current_work_style",
            "is_open_to_relocation",
            # Other fields
            "resume",
            "picture",
            "updated_at",
            "relationship_status",
            "skills",
            "education",
            "experience",
            "interests",
            # New Social Links Field (will be added automatically by the serializer)
            "social_links",
        ]
        read_only_fields = fields

    ### --- KEY CHANGE --- ###
    # This method now provides a comprehensive object for the frontend to easily
    # determine which icons and states to display.
    def get_relationship_status(self, obj):
        request = self.context.get("request")
        # Return None if there's no authenticated user making the request.
        if not request or not request.user.is_authenticated:
            return None

        current_user = request.user
        target_user = obj.user

        # Handle the case where a user is viewing their own profile.
        if target_user == current_user:
            return {
                "connection_status": "self",
                "is_followed_by_request_user": False,
            }

        # Determine the follow relationship status.
        # is_followed_by_request_user: Does the current user (A) follow the target user (B)?
        is_followed_by_request_user = Follow.objects.filter(
            follower=current_user, following=target_user
        ).exists()
        # is_following_request_user: Does the target user (B) follow the current user (A)?
        is_following_request_user = Follow.objects.filter(
            follower=target_user, following=current_user
        ).exists()

        connection_status = "not_connected"
        # A 'connected' state is defined by a mutual follow.
        if is_followed_by_request_user and is_following_request_user:
            connection_status = "connected"
        # Check if the current user has sent a pending request to the target.
        elif ConnectionRequest.objects.filter(
            sender=current_user, receiver=target_user, status="pending"
        ).exists():
            connection_status = "request_sent"
        # Check if the current user has received a pending request from the target.
        elif ConnectionRequest.objects.filter(
            sender=target_user, receiver=current_user, status="pending"
        ).exists():
            connection_status = "request_received"

        # Return the complete status object.
        return {
            "connection_status": connection_status,
            "is_followed_by_request_user": is_followed_by_request_user,
        }


# --- REPLACE your existing UserProfileUpdateSerializer with this one ---
# --- REPLACE your existing UserProfileUpdateSerializer with this complete version ---


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    # Define the nested serializer for incoming data. It's not read-only.
    social_links = SocialLinkSerializer(many=True, required=False)

    # Define fields for file uploads
    picture = serializers.ImageField(required=False, allow_null=True, use_url=False)
    resume = serializers.FileField(required=False, allow_null=True, use_url=False)

    class Meta:
        model = UserProfile
        fields = [
            # Standard text fields
            "display_name",
            "headline",
            "bio",
            # New Location Fields
            "location_city",
            "location_administrative_area",
            "location_country",
            "current_work_style",
            "is_open_to_relocation",
            # File and Array Fields
            "picture",
            "resume",
            "interests",
            # The key for our nested data
            "social_links",  # <--- THIS IS NOW CORRECTLY INCLUDED
        ]

    @transaction.atomic
    def update(self, instance, validated_data):
        # Pop the nested social_links data. If not provided, it will be None.
        social_links_data = validated_data.pop("social_links", None)

        # First, update the simple fields on the UserProfile model itself.
        instance = super().update(instance, validated_data)

        # Only proceed with link logic if 'social_links' was part of the request payload.
        if social_links_data is not None:
            # First, delete all existing links for this profile.
            # This is the simplest and most foolproof way to sync the state.
            instance.social_links.all().delete()

            # Now, re-create the links from the incoming data.
            # The frontend is the "source of truth" for what the links should be.
            links_to_create = [
                SocialLink(
                    profile=instance,
                    link_type=link_data["link_type"],
                    url=link_data["url"],
                )
                for link_data in social_links_data
            ]

            # Use bulk_create for efficiency.
            if links_to_create:
                SocialLink.objects.bulk_create(links_to_create)

        return instance


# --- END OF REPLACEMENT ---


# --- HEAVILY REFACTORED StatusPostSerializer with UPDATE logic ---
# In community/serializers.py

# --- HEAVILY REFACTORED StatusPostSerializer with UPDATE logic ---
# --- REPLACEMENT StatusPostSerializer with Polls and Fixes ---
# In C:\Users\Vinay\Project\Loopline\community\serializers.py


# --- REPLACEMENT FOR StatusPostSerializer ---
class StatusPostSerializer(serializers.ModelSerializer):

    class SimpleGroupSerializer(serializers.ModelSerializer):
        class Meta:
            model = Group
            fields = ["id", "name", "slug"]

    author = UserSerializer(read_only=True)
    is_liked_by_user = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    content_type_id = serializers.SerializerMethodField()
    object_id = serializers.SerializerMethodField()
    post_type = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    # This is the new unified field that accepts slugs for writing.
    group = serializers.SlugRelatedField(
        slug_field="slug", queryset=Group.objects.all(), required=False, allow_null=True
    )

    # All other field definitions are identical to your original code.
    media = PostMediaSerializer(many=True, read_only=True)
    images = serializers.ListField(
        child=serializers.FileField(use_url=False), write_only=True, required=False
    )
    videos = serializers.ListField(
        child=serializers.FileField(use_url=False), write_only=True, required=False
    )
    media_to_delete = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    poll = PollSerializer(read_only=True, allow_null=True)
    poll_data = serializers.CharField(write_only=True, required=False, allow_blank=True)
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = StatusPost
        # 'group_id' has been removed from this list.
        fields = [
            "id",
            "author",
            "content",
            "created_at",
            "updated_at",
            "group",
            "like_count",
            "is_liked_by_user",
            "content_type_id",
            "object_id",
            "post_type",
            "comment_count",
            "media",
            "images",
            "videos",
            "media_to_delete",
            "poll",
            "poll_data",
            "is_saved",
        ]
        # The read_only_fields are identical to your original code.
        read_only_fields = [
            "id",
            "author",
            "created_at",
            "updated_at",
            "like_count",
            "is_liked_by_user",
            "content_type_id",
            "object_id",
            "post_type",
            "comment_count",
            "media",
            "poll",
            "group",
            "is_saved",
        ]

    # This new method formats the group data correctly when you READ a post.
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.group:
            representation["group"] = self.SimpleGroupSerializer(
                instance.group, context=self.context
            ).data
        return representation

    # ALL of your existing validation, create, update, and get methods below this line
    # are IDENTICAL to the code you provided and are included here.

    def validate_media_to_delete(self, value):
        if not value:
            return []
        try:
            ids = json.loads(value)
            if not isinstance(ids, list):
                raise serializers.ValidationError(
                    "media_to_delete must be a JSON-formatted array."
                )
            return [int(id_val) for id_val in ids]
        except (json.JSONDecodeError, ValueError, TypeError):
            raise serializers.ValidationError(
                "Invalid format. media_to_delete must be a JSON-formatted array of integers."
            )

    def validate_poll_data(self, value):
        if not value:
            return None
        try:
            data = json.loads(value)
            if not isinstance(data, dict):
                raise serializers.ValidationError("Poll data must be a JSON object.")
            if "question" not in data or not str(data["question"]).strip():
                raise serializers.ValidationError("Poll question cannot be empty.")
            is_update_payload = (
                "options_to_update" in data
                or "options_to_add" in data
                or "options_to_delete" in data
            )
            if is_update_payload:
                if "options_to_update" in data and not isinstance(
                    data["options_to_update"], list
                ):
                    raise serializers.ValidationError(
                        "options_to_update must be a list."
                    )
                if "options_to_add" in data and not isinstance(
                    data["options_to_add"], list
                ):
                    raise serializers.ValidationError("options_to_add must be a list.")
                if "options_to_delete" in data and not isinstance(
                    data["options_to_delete"], list
                ):
                    raise serializers.ValidationError(
                        "options_to_delete must be a list."
                    )
            else:
                if "options" not in data or not isinstance(data["options"], list):
                    raise serializers.ValidationError("Poll options must be a list.")
                if len(data["options"]) < 2:
                    raise serializers.ValidationError(
                        "A poll must have at least two options."
                    )
                if any(not str(opt).strip() for opt in data["options"]):
                    raise serializers.ValidationError("Poll options cannot be empty.")
            return data
        except json.JSONDecodeError:
            raise serializers.ValidationError("Invalid JSON format for poll data.")

    def validate(self, data):
        is_update = self.instance is not None
        content = (
            data.get("content", self.instance.content if is_update else None) or ""
        ).strip()
        new_images = data.get("images", [])
        new_videos = data.get("videos", [])
        poll_data = data.get("poll_data")
        if is_update:
            media_to_delete_ids = data.get("media_to_delete", [])
            surviving_media_count = self.instance.media.exclude(
                id__in=media_to_delete_ids
            ).count()
            final_media_count = (
                surviving_media_count + len(new_images) + len(new_videos)
            )
            if not content and final_media_count == 0 and not poll_data:
                raise serializers.ValidationError(
                    "A post cannot be empty. It must have text content, media, or a poll."
                )
        else:
            if not content and not new_images and not new_videos and not poll_data:
                raise serializers.ValidationError(
                    "A post must have text content, media, or a poll."
                )
        return data

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request")
        images_data = validated_data.pop("images", [])
        videos_data = validated_data.pop("videos", [])
        poll_data = validated_data.pop("poll_data", None)
        validated_data.pop("media_to_delete", None)
        if poll_data:
            validated_data["content"] = poll_data.get("question", "")
        validated_data["author"] = request.user
        post = StatusPost.objects.create(**validated_data)
        media_to_create = []
        for image_file in images_data:
            media_to_create.append(
                PostMedia(post=post, media_type="image", file=image_file)
            )
        for video_file in videos_data:
            media_to_create.append(
                PostMedia(post=post, media_type="video", file=video_file)
            )
        if media_to_create:
            PostMedia.objects.bulk_create(media_to_create)
        if poll_data:
            poll = Poll.objects.create(post=post, question=poll_data["question"])
            poll_options_to_create = [
                PollOption(poll=poll, text=option_text)
                for option_text in poll_data["options"]
            ]
            PollOption.objects.bulk_create(poll_options_to_create)
        if post.content:
            process_mentions(
                actor=request.user, target_object=post, content_text=post.content
            )
        return post

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get("request")
        images_data = validated_data.pop("images", [])
        videos_data = validated_data.pop("videos", [])
        media_to_delete_ids = validated_data.pop("media_to_delete", [])
        poll_data = validated_data.pop("poll_data", None)
        original_content = instance.content
        instance = super().update(instance, validated_data)
        if media_to_delete_ids:
            instance.media.filter(id__in=media_to_delete_ids).delete()
        media_to_create = []
        for image_file in images_data:
            media_to_create.append(
                PostMedia(post=instance, media_type="image", file=image_file)
            )
        for video_file in videos_data:
            media_to_create.append(
                PostMedia(post=instance, media_type="video", file=video_file)
            )
        if media_to_create:
            PostMedia.objects.bulk_create(media_to_create)
        if poll_data and hasattr(instance, "poll"):
            poll = instance.poll
            poll.question = poll_data.get("question", poll.question)
            poll.save()
            options_to_delete_ids = poll_data.get("options_to_delete", [])
            if options_to_delete_ids:
                PollOption.objects.filter(
                    id__in=options_to_delete_ids, poll=poll
                ).delete()
            options_to_update = poll_data.get("options_to_update", [])
            for option_data in options_to_update:
                option_id = option_data.get("id")
                option_text = option_data.get("text")
                if option_id and option_text is not None:
                    PollOption.objects.filter(id=option_id, poll=poll).update(
                        text=option_text
                    )
            options_to_add = poll_data.get("options_to_add", [])
            if options_to_add:
                new_poll_options = [
                    PollOption(poll=poll, text=option_data.get("text"))
                    for option_data in options_to_add
                    if option_data.get("text")
                ]
                if new_poll_options:
                    PollOption.objects.bulk_create(new_poll_options)
        instance.save()
        if instance.content is not None and instance.content != original_content:
            process_mentions(
                actor=request.user,
                target_object=instance,
                content_text=instance.content,
            )
        return self.Meta.model.objects.get(pk=instance.pk)

    def get_is_saved(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.saved_by.filter(user=request.user).exists()

    def get_like_count(self, obj):
        return obj.likes.count() if hasattr(obj, "likes") else 0

    def get_is_liked_by_user(self, obj):
        user = self.context.get("request").user
        if user and user.is_authenticated:
            content_type = ContentType.objects.get_for_model(obj)
            return Like.objects.filter(
                content_type=content_type, object_id=obj.pk, user=user
            ).exists()
        return False

    def get_content_type_id(self, obj):
        return ContentType.objects.get_for_model(obj).id

    def get_object_id(self, obj):
        return obj.pk

    def get_post_type(self, obj):
        return obj.__class__.__name__.lower()

    def get_comment_count(self, obj):
        if obj and obj.pk:
            content_type = ContentType.objects.get_for_model(obj)
            return Comment.objects.filter(
                content_type=content_type, object_id=obj.pk
            ).count()
        return 0


# --- END OF REPLACEMENT FOR StatusPostSerializer ---


# --- THIS IS THE CORRECTED VERSION ---
class LivePostSerializer(serializers.ModelSerializer):
    """
    An extremely lightweight serializer for pushing only the ID of a new post
    over WebSockets, following the "True Hybrid" model.
    """

    class Meta:
        model = StatusPost
        fields = ["id"]  # We only need to send the ID.

    # ... (all get_* methods remain the same)


# --- FeedItemSerializer and other serializers remain unchanged ---
# ... (rest of your serializers.py file) ...
# --- CORRECTED FeedItemSerializer with proper indentation ---
class FeedItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    author = UserSerializer(read_only=True)
    content = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    like_count = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()
    content_type_id = serializers.SerializerMethodField()
    object_id = serializers.SerializerMethodField()
    post_type = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    media = PostMediaSerializer(many=True, read_only=True)
    poll = serializers.SerializerMethodField()

    def get_poll(self, obj):
        # Check if the object is a StatusPost and has a related poll
        if isinstance(obj, StatusPost) and hasattr(obj, "poll"):
            # The context containing the 'request' is automatically passed down
            return PollSerializer(obj.poll, context=self.context).data
        return None

    # CORRECT INDENTATION: This is now a method of the class

    # CORRECT INDENTATION: This is now a method of the class
    def get_post_type(self, obj):
        return obj.__class__.__name__.lower()

    # CORRECT INDENTATION: This is now a method of the class
    def get_title(self, obj):
        return getattr(obj, "title", None)

    # CORRECT INDENTATION: This is now a method of the class
    def get_like_count(self, obj):
        return obj.likes.count() if hasattr(obj, "likes") else 0

    # CORRECT INDENTATION: This is now a method of the class
    def get_is_liked_by_user(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        if obj.pk and hasattr(obj, "likes"):
            content_type = ContentType.objects.get_for_model(obj)
            return Like.objects.filter(
                content_type=content_type, object_id=obj.pk, user=request.user
            ).exists()
        return False

    # CORRECT INDENTATION: This is now a method of the class
    def get_content_type_id(self, obj):
        return ContentType.objects.get_for_model(obj).id

    # CORRECT INDENTATION: This is now a method of the class
    def get_object_id(self, obj):
        return obj.pk

    # CORRECT INDENTATION: This is now a method of the class
    def get_comment_count(self, obj):
        if obj and obj.pk:
            content_type = ContentType.objects.get_for_model(obj)
            return Comment.objects.filter(
                content_type=content_type, object_id=obj.pk
            ).count()
        return 0


# In community/serializers.py


class GroupSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    member_count = serializers.IntegerField(source="members.count", read_only=True)
    membership_status = serializers.SerializerMethodField()

    # --- CHANGE 1: 'members' is now a SerializerMethodField ---
    members = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "creator",
            "member_count",
            "membership_status",
            "created_at",
            "privacy_level",
            "members",
        ]
        read_only_fields = ["creator", "member_count", "created_at"]

    # NEW, FIXED METHOD
    def get_membership_status(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return "none"

        user = request.user

        # --- THIS IS THE FIX ---
        # Check for a block record first. It's the highest priority status.
        # The related_name on the Group model for GroupBlock is likely 'blocked_users_info' or similar.
        # Let's use the explicit model query which is safer.
        if GroupBlock.objects.filter(group=obj, user=user).exists():
            return "blocked"
        # --- END OF FIX ---

        if obj.creator == user:
            return "creator"

        if obj.members.filter(pk=user.pk).exists():
            return "member"

        if (
            obj.privacy_level == "private"
            and obj.join_requests.filter(user=user, status="pending").exists()
        ):
            return "pending"

        return "none"

    # --- CHANGE 2: The new method that contains our security logic ---
    def get_members(self, obj):
        """
        Conditionally returns the list of group members.
        - For public groups, always returns the member list.
        - For private groups, only returns the member list to other members/creator.
        - For non-members of private groups, returns an empty list.
        """
        membership_status = self.get_membership_status(obj)

        # Allow access if the group is public OR if the user is a member/creator
        if obj.privacy_level == "public" or membership_status in ["creator", "member"]:
            queryset = obj.members.all()
            # We must pass the context down to the UserSerializer
            # so it can correctly build absolute image URLs.
            return UserSerializer(queryset, many=True, context=self.context).data

        # For non-members of a private group, return a safe empty list
        return []


# =====================================================================================


class GroupJoinRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for listing and managing group join requests.
    This version uses a SerializerMethodField to guarantee context is passed.
    """

    # We change the field to a SerializerMethodField
    user = serializers.SerializerMethodField()

    class Meta:
        model = GroupJoinRequest
        fields = ["id", "user", "group", "status", "created_at"]
        read_only_fields = ["id", "group", "status", "created_at"]

    def get_user(self, obj):
        """
        This method manually serializes the user object.
        """
        # We explicitly create a UserSerializer instance for the user.
        # CRUCIALLY, we pass self.context, which we know contains the request,
        # down to the UserSerializer.
        serializer = UserSerializer(obj.user, context=self.context)

        # We return the serialized data.
        return serializer.data


class GroupBlockSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users who are blocked from a group.
    """

    user = UserSerializer(read_only=True)
    blocked_by = UserSerializer(read_only=True)

    class Meta:
        model = GroupBlock
        fields = ["id", "user", "group", "blocked_by", "created_at"]


# --- Replace your existing CommentSerializer with this one ---
class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(), allow_null=True, required=False
    )
    like_count = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()
    comment_content_type_id = serializers.SerializerMethodField(
        method_name="get_comment_content_type_id_for_like"
    )

    class Meta:
        model = Comment
        fields = [
            "id",
            "author",
            "content",
            "created_at",
            "updated_at",
            "content_type_id",
            "object_id",
            "parent",
            "like_count",
            "is_liked_by_user",
            "comment_content_type_id",
        ]
        read_only_fields = [
            "id",
            "author",
            "created_at",
            "updated_at",
            "content_type_id",
            "object_id",
            "like_count",
            "is_liked_by_user",
            "comment_content_type_id",
        ]

    def create(self, validated_data):
        """
        Custom create method to handle comment creation and mention processing.
        """
        # The view now provides all the context we need.
        request = self.context["request"]
        view = self.context["view"]

        content_type_model_name = view.kwargs.get("content_type").lower()
        object_id = view.kwargs.get("object_id")

        content_type = ContentType.objects.get(model=content_type_model_name)

        # Set the author and the generic foreign key fields
        validated_data["author"] = request.user
        validated_data["content_type"] = content_type
        validated_data["object_id"] = object_id

        # Create the comment instance
        comment = Comment.objects.create(**validated_data)

        # Now, process mentions in the comment's content
        if comment.content:
            process_mentions(
                actor=request.user, target_object=comment, content_text=comment.content
            )

        return comment

    def get_like_count(self, obj: Comment) -> int:
        return obj.likes.count()

    def get_is_liked_by_user(self, obj: Comment) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        comment_model_content_type = ContentType.objects.get_for_model(Comment)
        return Like.objects.filter(
            content_type=comment_model_content_type, object_id=obj.pk, user=request.user
        ).exists()

    def get_comment_content_type_id_for_like(self, obj: Comment) -> int:
        return ContentType.objects.get_for_model(Comment).id


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "conversation", "sender", "content", "timestamp"]
        read_only_fields = ["id", "sender", "timestamp"]


class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "participants", "created_at", "updated_at"]
        read_only_fields = ["id", "participants", "created_at", "updated_at"]


class MessageCreateSerializer(serializers.Serializer):
    recipient_username = serializers.CharField(max_length=150, write_only=True)
    content = serializers.CharField(write_only=True)

    def validate_recipient_username(self, value):
        if not User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Recipient user does not exist.")
        return value


# (Find the old CustomPasswordResetConfirmSerializer and replace it with this one)

# (Replace the entire CustomPasswordResetConfirmSerializer class with this)


class CustomPasswordResetConfirmSerializer(PasswordResetConfirmSerializer):
    """
    Final, definitive, and self-contained serializer for password reset.
    This version bypasses the flawed parent `validate` method entirely.
    It manually performs the required uid/token validation and then correctly
    translates field names ('new_password1' -> 'password1') for AllAuth's SetPasswordForm.
    """

    set_password_form_class = AllAuthSetPasswordForm

    def validate(self, attrs):
        from django.utils.encoding import force_str
        from allauth.account.forms import default_token_generator
        from allauth.account.utils import url_str_to_user_pk as uid_decoder

        try:
            uid = force_str(uid_decoder(attrs["uid"]))
            self.user = User._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"uid": ["Invalid value"]})

        if not default_token_generator.check_token(self.user, attrs["token"]):
            raise serializers.ValidationError({"token": ["Invalid value"]})

        # --- THIS IS THE FINAL, CORRECT TRANSLATION ---
        form_data = {
            "password1": attrs.get("new_password1"),
            "password2": attrs.get("new_password2"),
        }
        # --- END OF FIX ---

        self.set_password_form = self.set_password_form_class(
            user=self.user, data=form_data
        )
        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)

        return attrs

    def save(self):
        self.set_password_form.save()
        return self.user


class CustomLoginSerializer(LoginSerializer):
    """
    Custom login serializer that resends the verification email if a user
    with an unverified email address attempts to log in.
    """

    def validate(self, attrs):
        try:
            # First, run the standard validation from the parent class
            return super().validate(attrs)
        except serializers.ValidationError as e:
            # --- THIS IS THE CORRECTED LOGIC ---
            # The error detail from dj-rest-auth is a list of strings.
            # We check if our specific error message is present.
            is_unverified_email_error = (
                isinstance(e.detail, list)
                and e.detail
                and "E-mail is not verified." in e.detail[0]
            )

            if is_unverified_email_error:
                email_or_username = attrs.get("email") or attrs.get("username")
                if email_or_username:
                    try:
                        email_address = EmailAddress.objects.get(
                            email__iexact=email_or_username
                        )
                        email_address.send_confirmation()
                    except EmailAddress.DoesNotExist:
                        pass  # Should not happen in normal flow

            # CRITICAL: Always re-raise the original exception to ensure the login still fails
            raise e
