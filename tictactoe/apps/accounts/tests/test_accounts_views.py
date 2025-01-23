# Importiere notwendige Module und Klassen aus Django.
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

# Definiere eine Testklasse für die Registrierungsansicht.
class RegistrationViewTests(TestCase):
    def setUp(self):
        # Erstelle einen Client und setze die URL für die Registrierungsansicht.
        self.client = Client()
        self.url = reverse('accounts:register')
        # Erstelle einen Testbenutzer.
        self.user = get_user_model().objects.create_user(
            username='testuser', email='testuser@example.com', password='testpass123'
        )

    # Testet den GET-Request der Registrierungsansicht.
    def test_registration_view_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration.html')

    # Testet den erfolgreichen POST-Request der Registrierungsansicht.
    def test_registration_view_post_success(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'newpassword123',
            'password2': 'newpassword123'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)  # Weiterleitung zu core:home
        self.assertRedirects(response, reverse('core:home'))
        self.assertTrue(get_user_model().objects.filter(username='newuser').exists())
        self.assertTrue(get_user_model().objects.filter(email='newuser@example.com').exists())

    # Testet den fehlgeschlagenen POST-Request der Registrierungsansicht.
    def test_registration_view_post_failure(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'newpassword123',
            'password2': 'wrongpassword'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration.html')
        self.assertFormError(response, 'registration_form', 'password2', "The two password fields didn’t match.")

    # Testet den GET-Request der Registrierungsansicht für authentifizierte Benutzer.
    def test_registration_view_authenticated_user(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('core:home'))

    # Testet die Weiterleitung nach erfolgreicher Registrierung zu einer bestimmten URL.
    def test_registration_view_post_with_redirect(self):
        next_url = reverse('accounts:profile')  # Verwende eine vorhandene URL
        data = {
            'username': 'redirectuser',
            'email': 'redirectuser@example.com',
            'password1': 'redirectpassword123',
            'password2': 'redirectpassword123'
        }
        response = self.client.post(f"{self.url}?next={next_url}", data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, next_url)
        self.assertTrue(get_user_model().objects.filter(username='redirectuser').exists())
        self.assertTrue(get_user_model().objects.filter(email='redirectuser@example.com').exists())

# Definiere eine Testklasse für die Login-Ansicht.
class LoginViewTests(TestCase):
    def setUp(self):
        # Erstelle einen Client und setze die URL für die Login-Ansicht.
        self.client = Client()
        self.url = reverse('accounts:login')
        # Erstelle einen Testbenutzer.
        self.user = get_user_model().objects.create_user(
            username='testuser', password='testpass123', email='testuser@example.com'
        )

    # Testet den GET-Request der Login-Ansicht.
    def test_login_view_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    # Testet den erfolgreichen POST-Request der Login-Ansicht.
    def test_login_view_post_success(self):
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)  # Weiterleitung zu core:home
        self.assertRedirects(response, reverse('core:home'))
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertTrue('jwt_token' in self.client.session)

    # Testet den fehlgeschlagenen POST-Request der Login-Ansicht.
    def test_login_view_post_failure(self):
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertFalse('_auth_user_id' in self.client.session)

    # Testet den GET-Request der Login-Ansicht für authentifizierte Benutzer.
    def test_login_view_authenticated_user(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('core:home'))

    # Testet die Weiterleitung nach erfolgreichem Login zu einer bestimmten URL.
    def test_login_view_post_with_redirect(self):
        next_url = reverse('accounts:profile')  # Verwende eine vorhandene URL
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(f"{self.url}?next={next_url}", data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, next_url)
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertTrue('jwt_token' in self.client.session)

# Definiere eine Testklasse für die Logout-Ansicht.
class LogoutViewTests(TestCase):
    def setUp(self):
        # Erstelle einen Client und setze die URL für die Logout-Ansicht.
        self.client = Client()
        self.logout_url = reverse('accounts:logout')
        self.login_url = reverse('accounts:login')
        # Erstelle einen Testbenutzer.
        self.user = get_user_model().objects.create_user(
            username='testuser', password='testpass123', email='testuser@example.com'
        )

    # Testet die Logout-Ansicht.
    def test_logout_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.login_url)
        self.assertFalse('_auth_user_id' in self.client.session)
        self.assertFalse('jwt_token' in self.client.session)
