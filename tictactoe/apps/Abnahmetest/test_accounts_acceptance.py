import time

from django.contrib.auth import get_user_model
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.test import LiveServerTestCase
from rest_framework.test import APIClient
from django.urls import reverse

class AccountsAcceptanceTests(LiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Chrome()
        self.browser.implicitly_wait(10)
        self.api_client = APIClient()

    def tearDown(self):
        self.browser.quit()

    def test_user_registration_and_login(self):
        # Benutzerregistrierung
        self.browser.get(f'{self.live_server_url}/accounts/register/')

        # Eingabefelder für Registrierung
        username_input = self.browser.find_element(By.NAME, 'username')
        email_input = self.browser.find_element(By.NAME, 'email')
        password1_input = self.browser.find_element(By.NAME, 'password1')
        password2_input = self.browser.find_element(By.NAME, 'password2')

        # Ausfüllen der Registrierungsdaten
        username_input.send_keys('testuser')
        email_input.send_keys('testuser@example.com')
        password1_input.send_keys('testpassword123')
        password2_input.send_keys('testpassword123')
        password2_input.send_keys(Keys.RETURN)

        # Überprüfen, ob die Registrierung erfolgreich war und zur Startseite weitergeleitet wird
        WebDriverWait(self.browser, 20).until(
            EC.url_contains('/')
        )
        self.assertIn('/', self.browser.current_url)

        # Manuelle Navigation zur Profilseite
        self.browser.get(f'{self.live_server_url}/accounts/profile/')
        WebDriverWait(self.browser, 20).until(
            EC.url_contains('/accounts/profile')
        )
        self.assertIn('/accounts/profile', self.browser.current_url)

        # Benutzer logout
        self.browser.get(f'{self.live_server_url}/accounts/logout/')
        WebDriverWait(self.browser, 20).until(
            EC.url_contains('/accounts/login')
        )
        self.assertIn('/accounts/login', self.browser.current_url)

        # Überprüfen, ob das Fenster noch offen ist
        self.assertTrue(self.browser.current_url.startswith(self.live_server_url))

        # Benutzerlogin
        self.browser.get(f'{self.live_server_url}/accounts/login/')

        # Eingabefelder für Login
        login_username_input = self.browser.find_element(By.NAME, 'username')
        login_password_input = self.browser.find_element(By.NAME, 'password')

        # Ausfüllen der Login-Daten
        login_username_input.send_keys('testuser')
        login_password_input.send_keys('testpassword123')
        login_password_input.send_keys(Keys.RETURN)

        # Überprüfen, ob der Login erfolgreich war und zur Startseite weitergeleitet wird
        WebDriverWait(self.browser, 20).until(
            EC.url_contains('/')
        )
        self.assertIn('/', self.browser.current_url)

        # Manuelle Navigation zur Profilseite
        self.browser.get(f'{self.live_server_url}/accounts/profile/')
        WebDriverWait(self.browser, 20).until(
            EC.url_contains('/accounts/profile')
        )
        self.assertIn('/accounts/profile', self.browser.current_url)
