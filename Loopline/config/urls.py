# C:\Users\Vinay\Project\Loopline\config\urls.py

"""
URL configuration for config project.
... (docstring) ...
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

# Import all necessary views from the community app
from community.views import ForcefulLogoutView, CustomConfirmEmailView, password_reset_redirect_view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('api/auth/logout/', ForcefulLogoutView.as_view(), name='forceful_rest_logout'),

    re_path(
        r'^api/auth/registration/account-confirm-email/(?P<key>[-:\w]+)/$',
        CustomConfirmEmailView.as_view(),
        name='account_confirm_email'
    ),

    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),

    # This URL bridges the backend email link to the frontend page.
    path(
        'password-reset/<str:uidb64>/<str:token>/',
        password_reset_redirect_view,
        name='password_reset_confirm'
    ),

    path('api/', include('community.urls', namespace='community')),
]

# The rest of your file remains unchanged
if settings.DEBUG:
    # --- TYPO FIX IS HERE ---
    urlpatterns.append(
        path('api/test/', include('e2e_test_utils.urls'))
    )
    # --- END OF FIX ---

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)