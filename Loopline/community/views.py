# community/views.py
from allauth.account.views import ConfirmEmailView
from django.db.models import Q, Count
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import logout as django_logout
from django.shortcuts import get_object_or_404, redirect
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.db.models import Q, Count, Value, CharField, Case, When
from django.db import transaction
from django.utils import timezone

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from rest_framework import (
    generics,
    status,
    views,
    serializers,
    permissions,
    viewsets,
    mixins,
)
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework.pagination import (
    PageNumberPagination,
    CursorPagination,
)  # NEW: Import CursorPagination
from rest_framework.filters import SearchFilter
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, permission_classes, action

# from dj_rest_auth.views import LogoutView


from .models import (
    UserProfile,
    Follow,
    StatusPost,
    Group,
    Comment,
    Like,
    Conversation,
    Message,
    Notification,
    Poll,
    PollOption,
    PollVote,
    Report,
    GroupJoinRequest,
    GroupBlock,
    ConnectionRequest,
    Follow,
    Skill,
    Education,
    Experience,
)
from .serializers import (
    UserSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    StatusPostSerializer,
    GroupSerializer,
    GroupJoinRequestSerializer,
    CommentSerializer,
    ConversationSerializer,
    MessageSerializer,
    MessageCreateSerializer,
    NotificationSerializer,
    ReportSerializer,
    GroupBlockSerializer,
    ConnectionRequestCreateSerializer,
    ConnectionRequestListSerializer,
    SkillSerializer,
    EducationSerializer,
    ExperienceSerializer,
)
from .permissions import (
    IsOwnerOrReadOnly,
    IsGroupMember,
    IsCreatorOrReadOnly,
    IsGroupCreator,
    IsGroupMemberOrPublicReadOnly,
)

User = get_user_model()

# ==================================
# Custom Pagination Classes
# ==================================


# Standard PageNumberPagination for less dynamic lists (e.g., search results, saved posts)
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


# NEW: CursorPagination for dynamic feeds (Main Feed, Group Feeds)
class PostCursorPagination(CursorPagination):
    page_size = 10
    ordering = (
        "-created_at",
        "-id",
    )  # Crucial for cursor pagination: Must match queryset ordering
    page_size_query_param = "page_size"  # Allow client to specify page size


# ==================================
# User Profile & Follower Views
# ==================================
class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    queryset = UserProfile.objects.select_related("user").all()
    lookup_field = "user__username"
    lookup_url_kwarg = "username"

    def get_serializer_class(self):
        return (
            UserProfileUpdateSerializer
            if self.request.method in ["PUT", "PATCH"]
            else UserProfileSerializer
        )

    def get_permissions(self):
        return (
            [IsAuthenticated(), IsOwnerOrReadOnly()]
            if self.request.method in ["PUT", "PATCH"]
            else [AllowAny()]
        )

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "request": self.request}

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_serializer = UserProfileSerializer(
            instance, context=self.get_serializer_context()
        )
        return Response(response_serializer.data)


class BaseProfileSectionViewSet(viewsets.ModelViewSet):
    """
    A base ViewSet that provides common functionality for profile sections
    like Education, Experience, and Skills. It handles permissions and
    queryset filtering automatically.
    """

    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        """
        This queryset ensures that users can only see and edit their own
        profile items. It filters based on the `username` from the URL.
        """
        username = self.kwargs.get("username")
        user = get_object_or_404(User, username=username)
        # The `self.queryset` is defined in the child classes (e.g., Education.objects.all())
        return self.queryset.filter(user=user)

    def perform_create(self, serializer):
        """
        When creating a new item, automatically assign it to the user
        specified in the URL.
        """
        username = self.kwargs.get("username")
        user = get_object_or_404(User, username=username)
        serializer.save(user=user)


class EducationViewSet(viewsets.ModelViewSet):
    """
    Manages CRUD operations for the authenticated user's education history.
    """

    serializer_class = EducationSerializer
    # Now consistent with ExperienceViewSet
    permission_classes = [
        permissions.IsAuthenticated,
        IsOwnerOrReadOnly,
    ]  # Ensures only logged-in users can access.

    def get_queryset(self):
        """
        This method is the key to security. It ensures that a user can ONLY
        ever see and interact with their own education entries.
        """
        # self.request.user.profile gives us the UserProfile of the logged-in user.
        return self.request.user.profile.education_history.all()

    def perform_create(self, serializer):
        """
        When a new education entry is created, this method automatically
        links it to the profile of the currently logged-in user.
        """
        serializer.save(user_profile=self.request.user.profile)


class ExperienceViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for User Profile Experience.
    """

    serializer_class = ExperienceSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        # Return only the experience entries for the currently logged-in user's profile
        return Experience.objects.filter(user_profile=self.request.user.profile)

    def perform_create(self, serializer):
        # Automatically attach the new experience to the logged-in user's profile
        serializer.save(user_profile=self.request.user.profile)


class SkillViewSet(BaseProfileSectionViewSet):
    """
    API endpoint for Creating, Reading, Updating, and Deleting Skill entries.
    URL: /api/community/profiles/<username>/skills/
    """

    queryset = Skill.objects.all()
    serializer_class = SkillSerializer


class UserPostListView(generics.ListAPIView):
    serializer_class = StatusPostSerializer
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination  # KEEP: Offset pagination is fine for a user's own post list

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get("username"))
        return (
            StatusPost.objects.filter(author=user)
            .select_related("author__profile")
            .prefetch_related("likes", "media", "poll__options", "poll__votes")
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        return {"request": self.request}


# --- FIND AND REPLACE THE ENTIRE FollowToggleView CLASS ---

# C:\Users\Vinay\Project\Loopline\community\views.py

# C:\Users\Vinay\Project\Loopline\community\views.py

# --- FINAL, CORRECTED FollowToggleView ---

# C:\Users\Vinay\Project\Loopline\community\views.py

# --- FINAL, CORRECTED FollowToggleView ---


class FollowToggleView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, username, format=None):
        """
        Allows current_user to follow the target 'username'.
        If this action results in a mutual follow, it establishes a 'connected' state.
        """
        user_to_follow = get_object_or_404(User, username__iexact=username)
        current_user = request.user

        if current_user == user_to_follow:
            return Response(
                {"detail": "You cannot follow yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # Create the follow from the current user to the target user.
            _, created_follow = Follow.objects.get_or_create(
                follower=current_user, following=user_to_follow
            )

            # --- KEY CHANGE: Check for conditions that create a mutual connection ---
            # Condition 1: Does the target user already follow the current user?
            is_reciprocal_follow = Follow.objects.filter(
                follower=user_to_follow, following=current_user
            ).exists()

            # Condition 2: Does a pending connection request exist FROM the target user?
            pending_request_from_target = ConnectionRequest.objects.filter(
                sender=user_to_follow, receiver=current_user, status="pending"
            ).first()

            if is_reciprocal_follow or pending_request_from_target:
                # A mutual connection is now established.

                # Ensure the reciprocal follow exists (important for the request-based connection).
                Follow.objects.get_or_create(
                    follower=user_to_follow, following=current_user
                )

                # Find and accept any pending request between these two users, in either direction.
                # This covers all scenarios gracefully.
                ConnectionRequest.objects.filter(
                    (
                        Q(sender=current_user, receiver=user_to_follow)
                        | Q(sender=user_to_follow, receiver=current_user)
                    ),
                    status="pending",
                ).update(status="accepted")

                return Response({"status": "connected"}, status=status.HTTP_200_OK)

            # If no connection was made, and a new follow was created, return 'following'.
            if created_follow:
                return Response({"status": "following"}, status=status.HTTP_201_CREATED)
            else:
                # If the follow already existed and no connection was made, it's a no-op.
                return Response(
                    {"detail": "You are already following this user."},
                    status=status.HTTP_200_OK,
                )

    def delete(self, request, username, format=None):
        """
        Allows current_user to unfollow the target 'username'.
        If this breaks a mutual connection, it performs a full "disconnect".
        """
        user_to_unfollow = get_object_or_404(User, username__iexact=username)
        current_user = request.user

        with transaction.atomic():
            # --- KEY CHANGE: Check for mutual connection BEFORE deleting anything ---
            was_mutually_connected = (
                Follow.objects.filter(
                    follower=current_user, following=user_to_unfollow
                ).exists()
                and Follow.objects.filter(
                    follower=user_to_unfollow, following=current_user
                ).exists()
            )

            # Delete the current user's follow toward the target user.
            deleted_count, _ = Follow.objects.filter(
                follower=current_user, following=user_to_unfollow
            ).delete()

            if deleted_count == 0:
                return Response(
                    {"detail": "You were not following this user."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # --- KEY CHANGE: If they were connected, perform a full disconnect ---
            if was_mutually_connected:
                # Remove the reciprocal follow as well.
                Follow.objects.filter(
                    follower=user_to_unfollow, following=current_user
                ).delete()

                # Reset any 'accepted' ConnectionRequest between them to 'rejected'.
                # This allows them to send new requests in the future.
                ConnectionRequest.objects.filter(
                    (
                        Q(sender=current_user, receiver=user_to_unfollow)
                        | Q(sender=user_to_unfollow, receiver=current_user)
                    ),
                    status="accepted",
                ).update(status="rejected")

                return Response({"status": "disconnected"}, status=status.HTTP_200_OK)

            # If not mutually connected, it was just a simple unfollow.
            return Response({"status": "unfollowed"}, status=status.HTTP_200_OK)


class FollowingListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        target_user = get_object_or_404(User, username=self.kwargs["username"])
        return User.objects.filter(followers__follower=target_user)


class FollowersListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        target_user = get_object_or_404(User, username=self.kwargs["username"])
        return User.objects.filter(following__following=target_user)


# ==================================
# Connection Request Views
# ==================================
# C:\Users\Vinay\Project\Loopline\community\views.py


# --- REPLACE THE ENTIRE ConnectionRequestViewSet ---
class ConnectionRequestViewSet(
    mixins.ListModelMixin, viewsets.GenericViewSet  # We no longer use CreateModelMixin
):
    """
    ViewSet for sending (create) and listing (list) and managing Connection Requests.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        For 'list' action, returns pending requests received by the user.
        For 'detail' actions (accept/reject), returns the specific request.
        """
        if self.action == "list":
            return ConnectionRequest.objects.filter(
                receiver=self.request.user, status="pending"
            ).select_related("sender__profile")
        # For detail routes like accept/reject, get_object will handle lookup
        return ConnectionRequest.objects.all()

    def get_serializer_class(self):
        """
        Use a different serializer for creating vs. listing requests.
        """
        if self.action == "create":
            return ConnectionRequestCreateSerializer
        return ConnectionRequestListSerializer

    def create(self, request, *args, **kwargs):
        """
        Custom logic to create or re-activate a connection request.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        receiver = serializer.validated_data["receiver"]
        sender = request.user

        # Find any existing request between these two users, regardless of direction
        existing_request = ConnectionRequest.objects.filter(
            (Q(sender=sender, receiver=receiver) | Q(sender=receiver, receiver=sender))
        ).first()

        if existing_request:
            if existing_request.status == "pending":
                return Response(
                    {"detail": "A pending connection request already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if existing_request.status == "accepted":
                return Response(
                    {"detail": "You are already connected with this user."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # If a request was previously rejected, allow a new one by "resetting" it.
            if existing_request.status == "rejected":
                existing_request.sender = sender
                existing_request.receiver = receiver
                existing_request.status = "pending"
                existing_request.save()
                return_serializer = ConnectionRequestListSerializer(
                    existing_request, context={"request": request}
                )
                return Response(return_serializer.data, status=status.HTTP_200_OK)

        # If no request exists at all, create a new one.
        connection_request = ConnectionRequest.objects.create(
            sender=sender, receiver=receiver
        )
        return_serializer = ConnectionRequestListSerializer(
            connection_request, context={"request": request}
        )
        return Response(return_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        connection_request = get_object_or_404(
            ConnectionRequest, pk=pk, receiver=request.user, status="pending"
        )

        with transaction.atomic():
            connection_request.status = "accepted"
            connection_request.save()
            Follow.objects.get_or_create(
                follower=connection_request.sender,
                following=connection_request.receiver,
            )
            Follow.objects.get_or_create(
                follower=connection_request.receiver,
                following=connection_request.sender,
            )

        return Response(
            {"status": "Connection request accepted."}, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        connection_request = get_object_or_404(
            ConnectionRequest, pk=pk, receiver=request.user, status="pending"
        )

        connection_request.status = "rejected"
        connection_request.save()

        return Response(
            {"status": "Connection request rejected."}, status=status.HTTP_200_OK
        )


# C:\Users\Vinay\Project\Loopline\community\views.py


class AcceptConnectionRequestView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request, username, format=None):
        sender = get_object_or_404(User, username__iexact=username)
        receiver = request.user
        connection_request = get_object_or_404(
            ConnectionRequest, sender=sender, receiver=receiver, status="pending"
        )

        with transaction.atomic():
            connection_request.status = "accepted"
            connection_request.save()
            Follow.objects.get_or_create(follower=sender, following=receiver)
            Follow.objects.get_or_create(follower=receiver, following=sender)

        return Response(
            {"status": "Connection request accepted."}, status=status.HTTP_200_OK
        )


# ==================================
# Search Views
# ==================================
class UserSearchAPIView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = (
        StandardResultsSetPagination  # KEEP: Offset pagination for search results
    )

    def get_queryset(self):
        query = self.request.query_params.get("q", None)
        if not query or not query.strip():
            return User.objects.none()

        search_filter = (
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )

        queryset = (
            User.objects.filter(search_filter)
            .annotate(
                priority=Case(When(username__istartswith=query, then=1), default=2)
            )
            .distinct()
        )

        return queryset.order_by("priority", "username")


class ContentSearchAPIView(generics.ListAPIView):
    serializer_class = StatusPostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = (
        StandardResultsSetPagination  # KEEP: Offset pagination for search results
    )

    def get_queryset(self):
        query = self.request.query_params.get("q", None)
        if not query or not query.strip():
            return StatusPost.objects.none()

        queryset = (
            StatusPost.objects.filter(content__icontains=query)
            .select_related("author__profile")
            .prefetch_related("media", "likes", "poll__options", "poll__votes")
            .order_by("-created_at")
        )

        return queryset

    def get_serializer_context(self):
        return {"request": self.request}


# ==================================
# Status Post Views
# ==================================
class StatusPostListCreateView(generics.ListCreateAPIView):
    queryset = (
        StatusPost.objects.select_related("author__profile", "group__creator")
        .prefetch_related("likes", "media", "poll__options", "poll__votes")
        .order_by("-created_at")
    )
    serializer_class = StatusPostSerializer
    pagination_class = PageNumberPagination  # KEEP: This view handles both list (paginated) and create (not paginated)
    filter_backends = [SearchFilter]
    search_fields = ["content", "author__username"]

    def get_permissions(self):
        if self.request.method == "POST":
            # THE FIX: We now check for the 'group' key (which contains the slug)
            # instead of the old 'group_id' key. We also check that it's not empty.
            if "group" in self.request.data and self.request.data["group"]:
                return [IsAuthenticated(), IsGroupMember()]
            else:
                return [IsAuthenticated()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        group = serializer.validated_data.get("group", None)
        serializer.save(author=self.request.user, group=group)

    def get_serializer_context(self):
        return {"request": self.request}


class StatusPostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = (
        StatusPost.objects.select_related("author__profile")
        .prefetch_related("likes", "media", "poll__options", "poll__votes")
        .all()
    )
    serializer_class = StatusPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = "pk"

    def get_serializer_context(self):
        return {"request": self.request}


# ==================================
# Like View
# ==================================
# community/views.py


class LikeToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        content_type_id = kwargs.get("content_type_id")
        object_id = kwargs.get("object_id")

        content_type = get_object_or_404(ContentType, pk=content_type_id)
        target_object = get_object_or_404(content_type.model_class(), pk=object_id)

        like, created = Like.objects.get_or_create(
            user=request.user, content_type=content_type, object_id=target_object.id
        )

        if not created:
            # If 'created' is False, the like already existed, so we delete it (unlike).
            like.delete()
        # The 'else' block is now empty. A Django signal is responsible for creating
        # the notification and sending the real-time message. This prevents duplicates.

        return Response(
            {"liked": created, "like_count": target_object.likes.count()},
            status=status.HTTP_200_OK,
        )


# ==================================
# Moderation Views
# ==================================
class ReportCreateAPIView(generics.CreateAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["view"] = self
        return context


# In community/views.py


# Replace your existing PollVoteAPIView with this one.
class PollVoteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, poll_id, option_id, format=None):
        poll = get_object_or_404(Poll, pk=poll_id)
        option = get_object_or_404(PollOption, pk=option_id, poll=poll)

        # Use a database transaction to ensure data integrity
        with transaction.atomic():
            # Find out if the current user has already voted on this specific poll
            existing_vote = PollVote.objects.filter(
                user=request.user, poll=poll
            ).first()

            if existing_vote:
                if existing_vote.option == option:
                    # CASE 1: User clicked the same option again. We un-cast the vote.
                    existing_vote.delete()
                else:
                    # CASE 2: User changed their mind. We update the vote to the new option.
                    existing_vote.option = option
                    existing_vote.save()
            else:
                # CASE 3: User has not voted yet. We create a new vote.
                PollVote.objects.create(user=request.user, poll=poll, option=option)

        # After any change, we serialize the parent POST object. The serializer
        # is responsible for fetching the latest vote counts from the related 'votes' manager.
        # This is the "source of truth".
        post_instance = poll.post
        context = {"request": request}
        serializer = StatusPostSerializer(instance=post_instance, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ==================================
# Forum Views
# ==================================


# ==================================
# Group Views
# ==================================
class GroupListView(generics.ListCreateAPIView):
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = (
        StandardResultsSetPagination  # KEEP: Offset pagination for group discovery
    )

    filter_backends = [SearchFilter]
    search_fields = ["name", "description", "slug"]

    def get_queryset(self):
        return (
            Group.objects.select_related("creator__profile")
            .prefetch_related("members")
            .all()
        )

    def get_serializer_context(self):
        """
        Ensure the request object is passed to the serializer context.
        This is crucial for fields like 'is_member' and 'is_creator'.
        """
        return {"request": self.request}

    def perform_create(self, serializer):
        group = serializer.save(creator=self.request.user)
        group.members.add(self.request.user)


class GroupRetrieveAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.prefetch_related(
        "members__profile", "creator__profile"
    ).all()
    serializer_class = GroupSerializer
    permission_classes = [IsGroupMemberOrPublicReadOnly]  # <-- THIS IS THE FIX
    lookup_field = "slug"


# PASTE THIS ENTIRE CLASS TO REPLACE THE OLD ONE


class GroupMembershipView(APIView):
    permission_classes = [IsAuthenticated]

    # --- THE FIX IS HERE ---
    def post(self, request, slug, format=None):
        """
        Allows a user to join a public group directly or request to join a private group.
        """
        # --- AND HERE ---
        group = get_object_or_404(Group, slug=slug)
        user = request.user

        # === THIS IS THE NEW SECURITY CHECK ===
        # 1. Check if the user is blocked from this group BEFORE any other action.
        if GroupBlock.objects.filter(group=group, user=user).exists():
            return Response(
                {"detail": "You are blocked from joining this group."},
                status=status.HTTP_403_FORBIDDEN,
            )
        # ======================================

        # Prevent the user from joining/requesting if they are already a member.
        if group.members.filter(id=user.id).exists():
            return Response(
                {"detail": "You are already a member of this group."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- THIS IS THE NEW CORE LOGIC ---
        # ... inside GroupMembershipView's post method ...
        if group.privacy_level == "private":
            # For private groups, get or create a join request.
            join_request, created = GroupJoinRequest.objects.get_or_create(
                user=user, group=group
            )

            # --- THIS IS THE NEW, SMARTER LOGIC ---
            if not created:
                # If a request already exists...
                if join_request.status == "pending":
                    return Response(
                        {
                            "detail": "Your request to join this group is already pending."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                # If the user was previously approved (and left) or was denied,
                # allow them to re-request by resetting the status to pending.
                elif join_request.status in ["approved", "denied"]:
                    join_request.status = "pending"
                    join_request.save(update_fields=["status"])
                    # A signal on GroupJoinRequest will create the notification for the owner.

            # This response is now sent for both newly created requests
            # and for old requests that have been reset to 'pending'.
            return Response(
                {
                    "status": "request sent",
                    "detail": "Your request to join this private group has been sent.",
                },
                status=status.HTTP_201_CREATED,
            )
        # ... rest of the method

        else:
            # For public groups, add the member directly.
            group.members.add(user)
            return Response(
                {
                    "status": "member added",
                    "detail": f"Successfully joined the group '{group.name}'.",
                },
                status=status.HTTP_201_CREATED,
            )

    # --- AND HERE ---
    def delete(self, request, slug, format=None):
        """
        Allows a user to leave a group.
        """
        # --- AND HERE ---
        group = get_object_or_404(Group, slug=slug)
        user = request.user

        if not group.members.filter(id=user.id).exists():
            return Response(
                {"detail": "You are not a member of this group."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if group.creator == user:
            return Response(
                {
                    "detail": "Group creators cannot leave their own group. Please transfer ownership first."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        group.members.remove(user)
        return Response({"status": "member removed"}, status=status.HTTP_204_NO_CONTENT)


class GroupPostListView(generics.ListAPIView):
    serializer_class = StatusPostSerializer
    permission_classes = [AllowAny]
    pagination_class = PostCursorPagination  # NEW: Use cursor pagination here

    def get_queryset(self):
        # This line DEFINES the variable 'group_slug' by getting it from the URL
        group_slug = self.kwargs.get("slug")

        # This line USES the 'group_slug' variable we just defined
        return (
            StatusPost.objects.filter(group__slug=group_slug)
            .select_related("author__profile", "group")
            .prefetch_related("media", "likes", "poll__options", "poll__votes")
            .order_by("-created_at")
        )  # IMPORTANT: Must match cursor pagination ordering

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_serializer_context(self):
        return {"request": self.request}


# ==================================
# Comment Views
# ==================================
class CommentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None  # KEEP: No pagination for comments (show all)

    def get_queryset(self):
        content_type = get_object_or_404(
            ContentType, model=self.kwargs.get("content_type").lower()
        )
        parent_object = get_object_or_404(
            content_type.model_class(), pk=self.kwargs.get("object_id")
        )
        return (
            Comment.objects.filter(
                content_type=content_type, object_id=parent_object.id
            )
            .select_related("author__profile")
            .order_by("created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        context["view"] = self
        return context

    def perform_create(self, serializer):
        serializer.save()


class CommentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.select_related("author__profile").all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = "pk"


# ==================================
# Feed View
# ==================================
class FeedListView(generics.ListAPIView):
    serializer_class = StatusPostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PostCursorPagination
    authentication_classes = [TokenAuthentication]

    # THIS IS THE NEW, FIXED CODE
    def get_queryset(self):
        user = self.request.user

        # 1. Get the authors for the feed (unchanged)
        following_user_ids = list(user.following.values_list("following_id", flat=True))
        user_ids_for_feed = following_user_ids + [user.id]

        # 2. Define the privacy filter using Q objects
        # A post is visible in the feed if:
        # - It has no group (it's a personal, public wall post), OR
        # - Its group is public, OR
        # - Its group is private AND the current user is a member of that group.
        privacy_q = (
            Q(group__isnull=True)
            | Q(group__privacy_level="public")
            | Q(group__members=user)
        )

        # 3. Combine the filters and return the final queryset
        return (
            StatusPost.objects.filter(author_id__in=user_ids_for_feed)
            .filter(privacy_q)
            .select_related("author__profile", "group")
            .prefetch_related("media", "likes", "poll__options", "poll__votes")
            .order_by("-created_at", "-id")
            .distinct()
        )

    def get_serializer_context(self):
        return {"request": self.request}


# ==================================
# Saved Posts Views
# ==================================
class SavedPostToggleView(APIView):
    """
    Toggles saving or unsaving a post for the currently authenticated user.
    Expects a POST request to /api/community/posts/<pk>/save/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk, format=None):
        post = get_object_or_404(StatusPost, pk=pk)
        profile = request.user.profile

        if post in profile.saved_posts.all():
            profile.saved_posts.remove(post)
        else:
            profile.saved_posts.add(post)

        serializer = StatusPostSerializer(post, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class SavedPostListView(generics.ListAPIView):
    """
    Returns a paginated list of posts saved by the currently authenticated user.
    """

    serializer_class = StatusPostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = (
        StandardResultsSetPagination  # KEEP: Offset pagination for saved posts
    )

    def get_queryset(self):
        user = self.request.user
        return (
            user.profile.saved_posts.select_related("author__profile", "group")
            .prefetch_related("media", "likes", "poll__options", "poll__votes")
            .order_by("-created_at")
        )  # Order by most recently saved first, or by post creation date


# ==================================
# Private Messaging Views
# ==================================
class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination  # KEEP: Offset pagination for conversations

    def get_queryset(self):
        return self.request.user.conversations.prefetch_related(
            "participants__profile"
        ).order_by("-updated_at")


class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = (
        PageNumberPagination  # KEEP: Offset pagination for messages within conversation
    )

    def get_queryset(self):
        conversation = get_object_or_404(
            Conversation,
            pk=self.kwargs.get("conversation_id"),
            participants=self.request.user,
        )
        return conversation.messages.select_related("sender__profile").order_by(
            "timestamp"
        )


class SendMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        input_serializer = MessageCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        recipient = get_object_or_404(
            User, username=input_serializer.validated_data["recipient_username"]
        )
        if request.user == recipient:
            return Response(
                {"error": "You cannot send messages to yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        conversation = (
            Conversation.objects.filter(participants=request.user)
            .filter(participants=recipient)
            .annotate(p_count=Count("participants"))
            .filter(p_count=2)
            .first()
        )
        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, recipient)
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=input_serializer.validated_data["content"],
        )
        conversation.save()
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


# ==================================
# Notification Views
# ==================================
class NotificationListAPIView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = (
        StandardResultsSetPagination  # KEEP: Offset pagination for notifications
    )

    def get_queryset(self):
        return self.request.user.notifications_received.all().order_by("-timestamp")


class UnreadNotificationCountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        return Response(
            {
                "unread_count": request.user.notifications_received.filter(
                    is_read=False
                ).count()
            }
        )


class MarkNotificationAsReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, format=None):
        notification = get_object_or_404(request.user.notifications_received, pk=pk)

        if not notification.is_read:
            notification.is_read = True
            notification.save()

        new_unread_count = request.user.notifications_received.filter(
            is_read=False
        ).count()

        return Response({"unread_count": new_unread_count}, status=status.HTTP_200_OK)


class MarkMultipleNotificationsAsReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        ids = request.data.get("notification_ids", [])
        updated_count = request.user.notifications_received.filter(
            id__in=ids, is_read=False
        ).update(is_read=True)
        return Response({"detail": f"{updated_count} notification(s) marked as read."})


class MarkAllNotificationsAsReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        updated_count = request.user.notifications_received.filter(
            is_read=False
        ).update(is_read=True)
        return Response({"detail": f"{updated_count} notification(s) marked as read."})


# ==================================
# Group Management Views (New Section)
# ==================================


class GroupTransferOwnershipView(APIView):
    """
    API view to transfer the ownership of a group from the creator to another member.
    """

    # NOTE: You will need to add IsGroupCreator to your imports at the top of the file
    # from .permissions import IsOwnerOrReadOnly, IsGroupMember, IsCreatorOrReadOnly, IsGroupCreator
    permission_classes = [IsGroupCreator]

    def post(self, request, *args, **kwargs):
        # The IsGroupCreator permission already verified that the request.user is the creator
        # and that the group exists.

        group_slug = self.kwargs.get("slug")
        group = get_object_or_404(
            Group, slug=group_slug
        )  # Using get_object_or_404 is safer

        new_owner_id = request.data.get("new_owner_id")

        # 1. --- Basic Validation ---
        if not new_owner_id:
            return Response(
                {"detail": "A new owner ID must be provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            new_owner = User.objects.get(pk=new_owner_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "The selected user does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 2. --- Business Logic Validation ---
        # Check if the new owner is the current creator
        if new_owner == group.creator:
            return Response(
                {"detail": "You cannot transfer ownership to yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the new owner is actually a member of the group
        if not group.members.filter(pk=new_owner.pk).exists():
            return Response(
                {"detail": "The selected user is not a member of this group."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. --- Perform the Transfer ---
        group.creator = new_owner
        group.save()

        return Response(
            {"detail": f"Ownership successfully transferred to {new_owner.username}."},
            status=status.HTTP_200_OK,
        )


class GroupJoinRequestListView(generics.ListAPIView):
    """
    Lists pending join requests for a specific group.
    Only accessible by the group creator.
    """

    serializer_class = GroupJoinRequestSerializer
    permission_classes = [IsAuthenticated, IsGroupCreator]

    def get_queryset(self):
        group_slug = self.kwargs.get("slug")
        # The IsGroupCreator permission already ensures the user is the creator.
        # We filter for requests that are still 'pending'.
        return GroupJoinRequest.objects.filter(
            group__slug=group_slug, status="pending"
        ).select_related(
            "user__profile"
        )  # Eager load user data for efficiency


# In community/views.py, inside GroupJoinRequestManageView

# In C:\Users\Vinay\Project\Loopline\community\views.py

# Add this entire class to your views.py file.


class GroupJoinRequestManageView(APIView):
    """
    Allows a group creator to approve, deny, or deny_and_block a join request.
    """

    permission_classes = [IsAuthenticated, IsGroupCreator]

    def patch(self, request, slug, request_id, format=None):
        # The IsGroupCreator permission ensures the user owns the group (via 'slug')

        join_request = get_object_or_404(
            GroupJoinRequest, id=request_id, group__slug=slug, status="pending"
        )

        # === THIS IS THE FIX: Delete the old notification first ===
        Notification.objects.filter(
            recipient=request.user, action_object_object_id=join_request.id
        ).delete()
        # ==========================================================

        action = request.data.get("action")

        if action not in ["approve", "deny", "deny_and_block"]:
            return Response(
                {
                    "detail": "Invalid action. Must be 'approve', 'deny', or 'deny_and_block'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action == "approve":
            with transaction.atomic():
                join_request.status = "approved"
                join_request.group.members.add(join_request.user)
                join_request.save()

                # Create the approval notification for the user.
                Notification.objects.create(
                    recipient=join_request.user,
                    actor=request.user,  # The group owner is the actor
                    verb=f"approved your request to join the group",
                    notification_type=Notification.GROUP_JOIN_APPROVED,
                    target=join_request.group,
                )

            return Response(
                {"status": "Request approved. User added to group."},
                status=status.HTTP_200_OK,
            )

        if action == "deny":
            join_request.delete()
            return Response({"status": "Request denied."}, status=status.HTTP_200_OK)

        if action == "deny_and_block":
            with transaction.atomic():
                GroupBlock.objects.create(
                    group=join_request.group,
                    user=join_request.user,
                    blocked_by=request.user,
                )
                join_request.delete()

            return Response(
                {"status": "Request denied and user blocked."},
                status=status.HTTP_200_OK,
            )

        return Response(status=status.HTTP_400_BAD_REQUEST)


# In community/views.py


# Add this new view class
class GroupBlockListView(generics.ListAPIView):
    """
    Lists users who are blocked from a specific group.
    Only accessible by the group creator.
    """

    serializer_class = GroupBlockSerializer
    permission_classes = [IsAuthenticated, IsGroupCreator]
    pagination_class = StandardResultsSetPagination  # Re-use existing pagination

    def get_queryset(self):
        group_slug = self.kwargs.get("slug")
        # The IsGroupCreator permission already ensures the request.user is the creator.
        return GroupBlock.objects.filter(group__slug=group_slug).select_related(
            "user__profile", "blocked_by__profile"
        )


# In community/views.py


# Add this new view class
class GroupBlockManageView(APIView):
    """
    Allows a group creator to unblock a user by deleting the GroupBlock instance.
    """

    permission_classes = [IsAuthenticated, IsGroupCreator]

    def delete(self, request, slug, user_id, format=None):
        # The IsGroupCreator permission already ensures the request.user is the group creator.

        # We find the specific block record to delete.
        # This also implicitly checks that the group exists via the slug.
        group_block = get_object_or_404(GroupBlock, group__slug=slug, user__id=user_id)

        group_block.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


# Loopline/community/views.py

# ... (imports) ...


# Replace your existing ForcefulLogoutView with this one
class ForcefulLogoutView(APIView):
    """
    A custom, forceful logout view that takes complete control over the logout process.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if hasattr(request.user, "auth_token") and request.user.auth_token is not None:
            request.user.auth_token.delete()

        django_logout(request)

        response = Response(
            {"detail": "Successfully logged out."}, status=status.HTTP_200_OK
        )
        response.delete_cookie("sessionid", path="/")
        return response


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check_view(request):
    """
    A simple, lightweight endpoint to check if the server is responsive.
    Used by the frontend's navigation guards for proactive offline detection.
    """
    return Response({"status": "ok"}, status=status.HTTP_200_OK)


# --- ADD THIS ENTIRE CLASS AT THE END OF THE FILE ---


class CustomConfirmEmailView(ConfirmEmailView):

    def get(self, *args, **kwargs):
        try:
            # The get_object() method finds the confirmation object from the URL key
            self.object = self.get_object()
        except Http404:
            # If the key is invalid or expired, the object is not found.
            self.object = None

        if self.object:
            # --- THIS IS THE CRITICAL LINE WE WERE MISSING ---
            # The .confirm() method is what actually marks the email as verified in the database.
            self.object.confirm(self.request)

            # Now that the database is updated, we can safely show the success page.
            self.template_name = "account/account_email_confirm.html"
            return self.render_to_response(self.get_context_data())
        else:
            # If the key was invalid, we show the failure page.
            self.template_name = "account/email_confirmation_failed.html"
            return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["frontend_url"] = settings.FRONTEND_URL
        return context


def password_reset_redirect_view(request, uidb64, token):
    """
    Redirects the password reset link from the backend to the frontend app.
    """
    frontend_url = settings.FRONTEND_URL
    # We construct the full URL to our frontend's reset page
    return redirect(f"http://{frontend_url}/auth/reset-password/{uidb64}/{token}/")
