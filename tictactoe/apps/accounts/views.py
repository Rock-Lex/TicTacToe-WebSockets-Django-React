from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib import messages

from apps.accounts.forms import RegistrationForm, LoginForm, AvatarUploadForm
import logging

from apps.accounts.models import User

logger = logging.getLogger(__name__)


"""
Pages
"""


@login_required
def profile(request):
    try:
        logger.info("Rendering profile page for user: %s", request.user.username)
        return render(request, 'profile.html', {})
    except Exception as e:
        logger.error("Error rendering profile page: %s", str(e))
        messages.error(request, 'An error occurred while loading your profile.')
        return redirect('core:home')

"""
Login and Registration View
"""

class RegistrationView(View):

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logger.info("User %s attempted to access registration while logged in.", request.user.username)
            return redirect("core:home")
        return render(request, 'registration.html', {})

    def post(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                request.session['registration'] = "Successfully Registered"
                logger.info("User successfully registered.")
                return redirect("accounts:login")
            except Exception as e:
                logger.error("Error saving user registration: %s", str(e))
                messages.error(request, 'An error occurred during registration.')
        else:
            logger.warning("Invalid registration form submitted.")
            messages.error(request, 'Registration failed. Please correct the errors below.')
        return render(request, 'registration.html', {'registration_form': form})


class LoginView(View):

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logger.info("User %s attempted to access login while already logged in.", request.user.username)
            return redirect("core:home")
        context = {"Info": request.session.pop("registration", None)}
        return render(request, 'login.html', context)

    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                logger.info("User %s logged in successfully.", user.username)
                request.session['jwt_token'] = str(AccessToken.for_user(user))
                return redirect(get_redirect_if_exists(request) or 'core:home')
            else:
                logger.warning("Authentication failed for username: %s", username)
                messages.error(request, 'Invalid credentials. Please try again.')
        else:
            logger.warning("Invalid login form submitted.")
        return render(request, 'login.html', {'login_form': form})


class LogoutView(View):

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        try:
            logger.info("User %s logged out.", request.user.username)
            logout(request)
        except Exception as e:
            logger.error("Error during logout: %s", str(e))
            messages.error(request, 'An error occurred while logging out.')
        return redirect('accounts:login')


"""
User Update
"""


@login_required(login_url='/accounts/login')
def update_email(request):
    if request.method == "POST":
        return _process_email_update(request)
    return redirect('accounts:profile')


def _process_email_update(request):
    new_email = request.POST.get('new_email')
    if User.objects.filter(email=new_email).exists():
        logger.warning("Email update failed: email %s already in use.", new_email)
        messages.error(request, 'Email is already taken. Please use a different email.')
    else:
        try:
            request.user.email = new_email
            request.user.save()
            logger.info("User %s updated email to %s.", request.user.username, new_email)
            messages.success(request, 'Your email has been updated.')
        except Exception as e:
            logger.error("Error updating email for user %s: %s", request.user.username, str(e))
            messages.error(request, f'Failed to update email. Error: {e}')
    return redirect('accounts:profile')


@login_required(login_url='/accounts/login')
def update_password(request):
    if request.method == "POST":
        return _process_password_update(request)
    return redirect('accounts:profile')


def _process_password_update(request):
    password1 = request.POST.get('inputPassword1')
    password2 = request.POST.get('inputPassword2')

    if password1 != password2:
        logger.warning("Password update failed: passwords did not match.")
        messages.error(request, 'Passwords do not match.')
        return redirect('accounts:profile')

    try:
        request.user.set_password(password1)
        request.user.save()
        logger.info("User %s successfully updated password.", request.user.username)
        messages.success(request, 'Your password has been successfully updated.')
    except Exception as e:
        logger.error("Error updating password for user %s: %s", request.user.username, str(e))
        messages.error(request, f'Failed to update password. Error: {e}')
    return redirect('accounts:profile')


@login_required(login_url='/accounts/login')
def update_username(request):
    if request.method == "POST":
        return _process_username_update(request)
    return redirect('accounts:profile')


def _process_username_update(request):
    new_username = request.POST.get('new_username')
    if new_username == request.user.username:
        logger.warning("Username update failed: new username is the same as the current username.")
        messages.error(request, 'New username cannot be the same as the current one.')
    elif User.objects.filter(username=new_username).exists():
        logger.warning("Username update failed: username %s already in use.", new_username)
        messages.error(request, 'Username is already taken. Please choose another.')
    else:
        try:
            request.user.username = new_username
            request.user.save()
            logger.info("User %s updated username to %s.", request.user.username, new_username)
            messages.success(request, 'Your username has been successfully updated.')
        except Exception as e:
            logger.error("Error updating username for user %s: %s", request.user.username, str(e))
            messages.error(request, f'Failed to update username. Error: {e}')
    return redirect('accounts:profile')


@login_required
def upload_avatar(request):
    if request.method == "POST" and request.FILES:
        return _process_avatar_upload(request)
    return render(request, 'profile.html', {'form': AvatarUploadForm()})


def _process_avatar_upload(request):
    form = AvatarUploadForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            request.user.avatar = form.cleaned_data['avatar']
            request.user.save()
            logger.info("User %s updated avatar successfully.", request.user.username)
            messages.success(request, 'Your avatar has been updated.')
        except Exception as e:
            logger.error("Error uploading avatar for user %s: %s", request.user.username, str(e))
            messages.error(request, f'Failed to upload avatar. Error: {e}')
    else:
        logger.warning("Invalid avatar form submitted.")
        messages.error(request, 'Invalid avatar file. Please try again.')
    return redirect('accounts:profile')


"""
Utility Function
"""


def get_redirect_if_exists(request):
    """Fetches the redirect URL if available."""
    return request.GET.get("next")