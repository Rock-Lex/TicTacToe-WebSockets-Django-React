import logging

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from apps.accounts.models import User

logger = logging.getLogger('tictactoe')

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(max_length=255, help_text="Required. Add a valid email address.")

    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        try:
            user = User.objects.get(email=email)
        except Exception as e:
            return email
        raise forms.ValidationError(f"Email {email} is already in use.")

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = User.objects.get(username=username)
        except Exception as e:
            return username
        raise forms.ValidationError(f"Username {username} is already in use.")


class LoginForm(forms.ModelForm):
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'password')

    def clean(self):
        if self.is_valid():
            username = self.cleaned_data['username']
            password = self.cleaned_data['password']

            if not username or not password:
                logger.error("Username or password is missing in login form.")
                raise ValidationError("Both username and password must be provided.")

            user = authenticate(username=username, password=password)

            if user is None:
                logger.warning(f"Failed login attempt for username: {username}")
                raise ValidationError("Invalid username or password.")

            if not user.is_active:
                logger.warning(f"Attempt to log in with an inactive user: {username}")
                raise ValidationError("This account is inactive. Please contact support.")


class AvatarUploadForm(forms.Form):
    avatar = forms.ImageField()