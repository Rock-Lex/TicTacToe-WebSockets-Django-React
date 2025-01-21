# Import necessary modules and classes from Django.
from django.test import TestCase
from django.contrib.auth import get_user_model

# Define a test class for the User model.
class UserModelTests(TestCase):
    def setUp(self):
        # Get the User model.
        self.user_model = get_user_model()
        # Create a regular user.
        self.user = self.user_model.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        # Create a superuser.
        self.superuser = self.user_model.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123'
        )

    # Tests the creation of a regular user.
    def test_create_user(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'testuser@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_admin)

    # Tests the creation of a superuser.
    def test_create_superuser(self):
        self.assertEqual(self.superuser.username, 'adminuser')
        self.assertEqual(self.superuser.email, 'admin@example.com')
        self.assertTrue(self.superuser.check_password('adminpass123'))
        self.assertTrue(self.superuser.is_superuser)
        self.assertTrue(self.superuser.is_admin)

    # Tests the get_full_name method of the user.
    def test_get_full_name(self):
        self.assertEqual(self.user.get_full_name(), 'testuser@testuser')

    # Tests the get_short_name method of the user.
    def test_get_short_name(self):
        self.assertEqual(self.user.get_short_name(), 'testuser')

    # Tests if an email address is required.
    def test_email_is_required(self):
        with self.assertRaises(ValueError):
            self.user_model.objects.create_user(username='userwithoutemail', email='', password='testpass123')

    # Tests if the username is unique.
    def test_username_is_unique(self):
        with self.assertRaises(Exception):
            self.user_model.objects.create_user(username='testuser', email='newemail@example.com', password='newpass123')

    # Tests if the email address is unique.
    def test_email_is_unique(self):
        with self.assertRaises(Exception):
            self.user_model.objects.create_user(username='newuser', email='testuser@example.com', password='newpass123')

    # Tests the default fields for a user.
    def test_default_user_fields(self):
        user = self.user_model.objects.create_user(
            username='defaultuser',
            email='defaultuser@example.com',
            password='defaultpass123'
        )
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_admin)