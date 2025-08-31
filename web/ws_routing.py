from django.urls import re_path

from web.ws_consumers import WSConsumer_Create

websocket_urlpatterns = [
    re_path(r'ws/create/$', WSConsumer_Create.as_asgi()),
]