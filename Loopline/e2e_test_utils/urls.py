# C:\Users\Vinay\Project\Loopline\e2e_test_utils\urls.py

from django.urls import path
from .views import TestSetupAPIView  # <-- REMOVED the old, broken imports

urlpatterns = [
    # The new, consolidated endpoint for all test setup actions
    path('setup/', TestSetupAPIView.as_view(), name='test-setup'), 
]