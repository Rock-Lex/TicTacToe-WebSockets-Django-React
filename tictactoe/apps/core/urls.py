from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path('', views.home, name='home'),
    path('paginate-games/', views.paginate_games, name='paginate_games'),
]