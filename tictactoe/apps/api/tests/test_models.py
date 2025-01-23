from django.test import TestCase
from ..models import GameRoom, PlayedGame, generate_unique_code
from apps.accounts.models import User

class GameRoomAndPlayedGameTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser", email="testuser@example.com", password="<PASSWORD>")

    def test_generate_unique_code(self):
        game1 = PlayedGame.objects.create(winner=self.user, player_x=self.user, player_o=self.user)
        game2 = PlayedGame.objects.create(winner=self.user, player_x=self.user, player_o=self.user)
        self.assertNotEqual(game1.code, game2.code)

    def test_played_game_creation(self):
        game = PlayedGame.objects.create(winner=self.user, player_x=self.user, player_o=self.user)
        self.assertIsInstance(game, PlayedGame)
        self.assertEqual(game.winner, self.user)

    def test_game_room_unique_code(self):
        game_room = GameRoom.objects.create(host="session_key_1")
        game_room2 = GameRoom.objects.create(host="session_key_2")
        self.assertNotEqual(game_room.code, game_room2.code)

    def test_game_room_missing_player(self):
        game_room = GameRoom.objects.create(host="session_key_1")
        self.assertIsNone(game_room.player_x)
        self.assertIsNone(game_room.player_o)