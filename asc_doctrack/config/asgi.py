import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from config.ws_middleware import JWTAuthMiddlewareStack
import config.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = ProtocolTypeRouter({
    'http':      get_asgi_application(),
    'websocket': JWTAuthMiddlewareStack(
        URLRouter(config.routing.websocket_urlpatterns)
    ),
})
