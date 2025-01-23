# Import necessary modules and classes from Django.
from django.test import SimpleTestCase
from django.urls import reverse, resolve
from ..views import LoginView, LogoutView, profile, RegistrationView, update_email, update_password, update_username, upload_avatar

# Define a test class for the URLs of the Accounts app.
class TestUrls(SimpleTestCase):
    # Tests if the login URL resolves correctly.
    def test_login_url_resolves(self):
        url = reverse('accounts:login')
        self.assertEqual(resolve(url).func.view_class, LoginView)

    # Tests if the logout URL resolves correctly.
    def test_logout_url_resolves(self):
        url = reverse('accounts:logout')
        self.assertEqual(resolve(url).func.view_class, LogoutView)

    # Tests if the profile URL resolves correctly.
    def test_profile_url_resolves(self):
        url = reverse('accounts:profile')
        self.assertEqual(resolve(url).func, profile)

    # Tests if the registration URL resolves correctly.
    def test_register_url_resolves(self):
        url = reverse('accounts:register')
        self.assertEqual(resolve(url).func.view_class, RegistrationView)

    # Tests if the URL for updating the email resolves correctly.
    def test_update_email_url_resolves(self):
        url = reverse('accounts:update_email')
        self.assertEqual(resolve(url).func, update_email)

    # Tests if the URL for updating the password resolves correctly.
    def test_update_password_url_resolves(self):
        url = reverse('accounts:update_password')
        self.assertEqual(resolve(url).func, update_password)

    # Tests if the URL for updating the username resolves correctly.
    def test_update_username_url_resolves(self):
        url = reverse('accounts:update_username')
        self.assertEqual(resolve(url).func, update_username)

    # Tests if the URL for uploading the avatar resolves correctly.
    def test_upload_avatar_url_resolves(self):
        url = reverse('accounts:upload_avatar')
        self.assertEqual(resolve(url).func, upload_avatar)