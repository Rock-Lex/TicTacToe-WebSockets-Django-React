from django.urls import path
from .views import (
    RegistrationView,
    LoginView,
    LogoutView,
    profile,
    update_email,
    update_password,
    update_username,
    upload_avatar,
)

app_name = "accounts"

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),  # Updated to use CBV
    path('logout/', LogoutView.as_view(), name='logout'),  # Updated to use CBV
    path('register/', RegistrationView.as_view(), name='register'),  # Updated to use CBV
    path('profile/', profile, name='profile'),  # Function-based view remains unchanged
    path('update_email/', update_email, name='update_email'),  # Function-based view
    path('update_password/', update_password, name='update_password'),  # Function-based view
    path('update_username/', update_username, name='update_username'),  # Function-based view
    path('upload_avatar/', upload_avatar, name='upload_avatar'),  # Function-based view
]