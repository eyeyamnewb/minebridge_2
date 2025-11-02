# chat/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/chat/<room_id>/<sender_id>/<receiver_id>/', consumers.Chatconsumer.as_asgi()),
    path('ws/room_checker/<requesting_user>/<contact_user>/', consumers.room_checker_maker.as_asgi()),
    path('ws/notifications/',consumers.notificationConsumer.as_asgi())

]

# myproject/asgi.py
