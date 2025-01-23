from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.decorators import login_required

from .views import *
from . import views


app_name = "api"


urlpatterns = [
    path('get-tokens/', views.get_tokens, name='get_tokens'),
    path('game-room/', login_required(GameRoomView.as_view()), name='GameRoom'),
]