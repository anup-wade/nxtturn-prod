from .base import *
import os

# --------------------
# BASIC DEV SETTINGS
# --------------------
DEBUG = True

ALLOWED_HOSTS = ["*"]

# --------------------
# DATABASE (Docker)
# --------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

# --------------------
# CORS / CSRF
# --------------------
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

CORS_ALLOWED_ORIGINS = [FRONTEND_URL]
CSRF_TRUSTED_ORIGINS = [FRONTEND_URL]

# --------------------
# DEV TOOLS
# --------------------
INSTALLED_APPS += ["e2e_test_utils"]

# --------------------
# EMAIL (DEV SAFE)
# --------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "dev@localhost"
