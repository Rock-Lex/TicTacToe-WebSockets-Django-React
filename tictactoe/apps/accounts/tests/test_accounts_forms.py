from django.test import TestCase
from django.contrib.auth import get_user_model, authenticate
from ..forms import RegistrationForm, LoginForm

# Define a test class for the registration form.
class RegistrationFormTests(TestCase):
    def setUp(self):
        # Create an existing user in the database.
        self.user_model = get_user_model()
        self.user_model.objects.create_user(
            username='existinguser',
            email='existinguser@example.com',
            password='testpass123'
        )

    # Tests whether the registration form is valid with valid data.
    def test_registration_form_valid(self):
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        form = RegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    # Tests whether the registration form is invalid when the email already exists.
    def test_registration_form_existing_email(self):
        form_data = {
            'username': 'newuser2',
            'email': 'existinguser@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['email'], ['Email existinguser@example.com is already in use.'])

    # Tests whether the registration form is invalid when the username already exists.
    def test_registration_form_existing_username(self):
        form_data = {
            'username': 'existinguser',
            'email': 'newuser2@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['username'], ['Username existinguser is already in use.'])

    # Tests whether the registration form is invalid when the passwords do not match.
    def test_registration_form_password_mismatch(self):
        form_data = {
            'username': 'newuser3',
            'email': 'newuser3@example.com',
            'password1': 'testpass123',
            'password2': 'differentpass'
        }
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['password2'], ["The two password fields didn’t match."])

# Define a test class for the login form.
class LoginFormTests(TestCase):
    def setUp(self):
        # Create a valid user in the database.
        self.user_model = get_user_model()
        self.user_model.objects.create_user(
            username='validuser',
            email='validuser@example.com',
            password='testpass123'
        )

    # Tests whether the login form is valid with valid data.
    def test_login_form_valid(self):
        form_data = {
            'username': 'validuser',
            'password': 'testpass123'
        }
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())

    # Tests whether the login form is invalid when the password is incorrect.
    def test_login_form_invalid(self):
        form_data = {
            'username': 'validuser',
            'password': 'wrongpass'
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['__all__'], ['Invalid username or password.'])