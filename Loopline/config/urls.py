# C:\Users\Vinay\Project\Loopline\config\urls.py
"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

# Community / Auth views
from community.views import (
    ForcefulLogoutView,
    CustomConfirmEmailView,
    password_reset_redirect_view,
)

# --------------------------------------------------
# Health Check (for frontend / monitoring)
# --------------------------------------------------
def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    # --------------------------------------------------
    # Admin
    # --------------------------------------------------
    path("admin/", admin.site.urls),

    # --------------------------------------------------
    # Health Check (FIXES /health-check/ 404)
    # --------------------------------------------------
    path("health-check/", health_check, name="health_check"),
    path("healthz/", health_check),
    # --------------------------------------------------
    # Auth (dj-rest-auth)
    # --------------------------------------------------
    path(
        "api/auth/logout/",
        ForcefulLogoutView.as_view(),
        name="forceful_rest_logout",
    ),

    re_path(
        r"^api/auth/registration/account-confirm-email/(?P<key>[-:\w]+)/$",
        CustomConfirmEmailView.as_view(),
        name="account_confirm_email",
    ),

    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),

    # --------------------------------------------------
    # Password reset → frontend bridge
    # --------------------------------------------------
    path(
        "password-reset/<str:uidb64>/<str:token>/",
        password_reset_redirect_view,
        name="password_reset_confirm",
    ),

    # --------------------------------------------------
    # Community APIs
    # --------------------------------------------------
    path("api/", include(("community.urls", "community"), namespace="community")),
]

# --------------------------------------------------
# DEV / DEBUG ONLY
# --------------------------------------------------
if settings.DEBUG:
    urlpatterns.append(
        path("api/test/", include("e2e_test_utils.urls"))
    )
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )

