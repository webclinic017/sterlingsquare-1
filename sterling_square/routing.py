import cwebsocket.routing

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter(
            cwebsocket.routing.websocket_urlpatterns
        )
    ),
})

# from channels.sessions import SessionMiddlewareStack
# from channels.routing import ProtocolTypeRouter, URLRouter
#
# application = ProtocolTypeRouter({
#     # (http->django views is added by default)
#     'websocket': SessionMiddlewareStack(
#         URLRouter(
#             websocket.routing.websocket_urlpatterns
#         )
#     ),
# })