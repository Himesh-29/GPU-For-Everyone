"""ASGI config for GPU Connect — HTTP + WebSocket routing."""
import os

import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from channels.auth import AuthMiddlewareStack  # pylint: disable=wrong-import-position
from channels.routing import (  # pylint: disable=wrong-import-position
    ProtocolTypeRouter,
    URLRouter,
)

import computing.routing  # pylint: disable=wrong-import-position

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            computing.routing.websocket_urlpatterns
        )
    ),
})
