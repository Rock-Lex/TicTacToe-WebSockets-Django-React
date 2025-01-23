from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/main-chat-socket/', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/tictactoe-game-socket/(?P<room_code>[\w\d]+)/', consumers.GameRoomConsumer.as_asgi()),
    re_path(r'ws/(?P<room_code>[\w\d]+)/chat-socket/', consumers.GameRoomChatConsumer.as_asgi()),
    re_path(r'ws/search-queue/(?P<jwt_token>[\w\-\.\=\+]+)/(?P<host_code>[\w\d]+)/', consumers.SearchQueueConsumer.as_asgi())
]
