from .base import *
import os

DEBUG = True

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "34.30.48.239",
]

CSRF_TRUSTED_ORIGINS = [
    "http://34.30.48.239",
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "loopline",
        "USER": "loopline_user",
        "PASSWORD": "loopline_pass",
        "HOST": "127.0.0.1",
        "PORT": "5432",
    }
}



FRONTEND_URL = os.getenv("FRONTEND_URL")

CORS_ALLOWED_ORIGINS = [FRONTEND_URL]
CSRF_TRUSTED_ORIGINS = [FRONTEND_URL]

INSTALLED_APPS += ["e2e_test_utils"]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

