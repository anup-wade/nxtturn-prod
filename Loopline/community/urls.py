# community/urls.py
from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter, SimpleRouter

# Main router for standalone endpoints
router = DefaultRouter()
router.register(
    r"connections/requests",
    views.ConnectionRequestViewSet,
    basename="connection-request",
)

# Router for the LEGACY nested profile sections (Skills only)
profile_router = SimpleRouter()
profile_router.register(r"skills", views.SkillViewSet, basename="profile-skills")

# --- NEW: Unified Router for Profile Sections (Education & Experience) ---
profile_sections_router = SimpleRouter()
profile_sections_router.register(
    r"education", views.EducationViewSet, basename="profile-education"
)
profile_sections_router.register(
    r"experience", views.ExperienceViewSet, basename="profile-experience"
)


app_name = "community"

urlpatterns = [
    # --- NEW: Add the dedicated URL for the Education endpoint ---
    # This will create /api/community/profile/education/
    path("profile/", include(profile_sections_router.urls)),
    # --- User Profile, Follows, and Search ---
    # This path remains the same, but now only handles Experience and Skills from its nested router.
    path(
        "profiles/<str:username>/",
        include(
            [
                path(
                    "", views.UserProfileDetailView.as_view(), name="userprofile-detail"
                ),
                path("", include(profile_router.urls)),
            ]
        ),
    ),
    # ... (ALL OTHER URLS BELOW THIS LINE ARE UNCHANGED FROM YOUR ORIGINAL FILE) ...
    path(
        "users/<str:username>/posts/",
        views.UserPostListView.as_view(),
        name="user-post-list",
    ),
    path(
        "users/<str:username>/follow/",
        views.FollowToggleView.as_view(),
        name="follow-toggle",
    ),
    path(
        "users/<str:username>/following/",
        views.FollowingListView.as_view(),
        name="following-list",
    ),
    path(
        "users/<str:username>/followers/",
        views.FollowersListView.as_view(),
        name="followers-list",
    ),
    path(
        "users/<str:username>/accept-request/",
        views.AcceptConnectionRequestView.as_view(),
        name="user-accept-request",
    ),
    path("search/users/", views.UserSearchAPIView.as_view(), name="user-search"),
    path(
        "search/content/", views.ContentSearchAPIView.as_view(), name="content-search"
    ),
    path(
        "posts/",
        views.StatusPostListCreateView.as_view(),
        name="statuspost-list-create",
    ),
    path(
        "posts/<int:pk>/",
        views.StatusPostRetrieveUpdateDestroyView.as_view(),
        name="statuspost-detail",
    ),
    path(
        "content/<int:content_type_id>/<int:object_id>/like/",
        views.LikeToggleAPIView.as_view(),
        name="like-toggle",
    ),
    path(
        "content/<int:ct_id>/<int:obj_id>/report/",
        views.ReportCreateAPIView.as_view(),
        name="content-report",
    ),
    path("groups/", views.GroupListView.as_view(), name="group-list"),
    path(
        "groups/<slug:slug>/", views.GroupRetrieveAPIView.as_view(), name="group-detail"
    ),
    path(
        "groups/<slug:slug>/transfer-ownership/",
        views.GroupTransferOwnershipView.as_view(),
        name="group-transfer-ownership",
    ),
    path(
        "groups/<slug:slug>/membership/",
        views.GroupMembershipView.as_view(),
        name="group-membership",
    ),
    path(
        "groups/<slug:slug>/status-posts/",
        views.GroupPostListView.as_view(),
        name="group-statuspost-list",
    ),
    path(
        "groups/<slug:slug>/requests/",
        views.GroupJoinRequestListView.as_view(),
        name="group-join-requests-list",
    ),
    path(
        "groups/<slug:slug>/requests/<int:request_id>/",
        views.GroupJoinRequestManageView.as_view(),
        name="group-request-manage",
    ),
    path(
        "groups/<slug:slug>/blocks/",
        views.GroupBlockListView.as_view(),
        name="group-block-list",
    ),
    path(
        "groups/<slug:slug>/blocks/<int:user_id>/",
        views.GroupBlockManageView.as_view(),
        name="group-block-manage",
    ),
    path(
        "comments/<str:content_type>/<int:object_id>/",
        views.CommentListCreateAPIView.as_view(),
        name="comment-list-create",
    ),
    path(
        "comments/<int:pk>/",
        views.CommentRetrieveUpdateDestroyAPIView.as_view(),
        name="comment-detail",
    ),
    path("feed/", views.FeedListView.as_view(), name="user-feed"),
    path(
        "notifications/",
        views.NotificationListAPIView.as_view(),
        name="notification-list",
    ),
    path(
        "notifications/unread-count/",
        views.UnreadNotificationCountAPIView.as_view(),
        name="notification-unread-count",
    ),
    path(
        "notifications/<int:pk>/mark-as-read/",
        views.MarkNotificationAsReadAPIView.as_view(),
        name="notification-mark-as-read",
    ),
    path(
        "notifications/mark-as-read/",
        views.MarkMultipleNotificationsAsReadAPIView.as_view(),
        name="notifications-mark-as-read",
    ),
    path(
        "notifications/mark-all-as-read/",
        views.MarkAllNotificationsAsReadAPIView.as_view(),
        name="notifications-mark-all-as-read",
    ),
    path(
        "conversations/", views.ConversationListView.as_view(), name="conversation-list"
    ),
    path(
        "conversations/<int:conversation_id>/messages/",
        views.MessageListView.as_view(),
        name="message-list",
    ),
    path("messages/send/", views.SendMessageView.as_view(), name="send-message"),
    path(
        "polls/<int:poll_id>/options/<int:option_id>/vote/",
        views.PollVoteAPIView.as_view(),
        name="poll-vote",
    ),
    path(
        "posts/<int:pk>/save/",
        views.SavedPostToggleView.as_view(),
        name="post-save-toggle",
    ),
    path("posts/saved/", views.SavedPostListView.as_view(), name="saved-post-list"),
    path("health-check/", views.health_check_view, name="health-check"),
]

urlpatterns += router.urls
