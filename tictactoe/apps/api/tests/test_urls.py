from django.test import SimpleTestCase
from django.urls import reverse, resolve
from ..views import get_tokens, GameRoomView

class ApiURLsTests(SimpleTestCase):
    def test_get_tokens_url(self):
        url = reverse('api:get_tokens')
        self.assertEqual(url, '/api/get-tokens/')

    def test_game_room_url(self):
        url = reverse('api:GameRoom')
        self.assertEqual(url, '/api/game-room/')