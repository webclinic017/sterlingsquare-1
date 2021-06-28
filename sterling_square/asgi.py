"""
ASGI config for sterling_square project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# from sterling_square.websocket import websocket_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sterling_square.settings')

django_application = get_asgi_application()

import cwebsocket.routing
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter


# async def application(scope, receive, send):
#     if scope['type'] == 'http':
#         # Let Django handle HTTP requests
#         await django_application(scope, receive, send)
#     # elif scope['type'] == 'websocket':
#     #     await websocket_application(scope, receive, send)
#     else:
#         raise NotImplementedError(f"Unknown scope type {scope['type']}")


application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": django_application,

    # WebSocket handler
    "websocket": AuthMiddlewareStack(
        URLRouter(cwebsocket.routing.websocket_urlpatterns)
    ),
})


# async def websocket_applciation(scope, receive, send):
#     pass
