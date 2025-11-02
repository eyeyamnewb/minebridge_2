from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import mindapp.routing
from django.core.asgi import get_asgi_application

application = ProtocolTypeRouter({
        # (http->django views is added by default)
        "http": get_asgi_application(),
        'websocket': AuthMiddlewareStack(
            URLRouter(
                mindapp.routing.websocket_urlpatterns
            )
        ),
    })