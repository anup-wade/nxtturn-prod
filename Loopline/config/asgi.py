# C:\Users\Vinay\Project\Loopline\config\asgi.py

import os
from django.core.asgi import get_asgi_application

# This MUST be the first thing Django-related that happens.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# This line fully initializes the Django application, loads settings, etc.
django_asgi_app = get_asgi_application()

# NOW that Django is initialized, it is safe to import our other code.
from channels.routing import ProtocolTypeRouter, URLRouter

from community.middleware import TokenAuthMiddleware

import community.routing

application = ProtocolTypeRouter({
    # Standard HTTP requests are still handled by the Django app.
    "http": django_asgi_app,

    # WebSocket requests are now handled safely.
    "websocket": TokenAuthMiddleware(
        URLRouter(
            community.routing.websocket_urlpatterns
        )
    ),
})