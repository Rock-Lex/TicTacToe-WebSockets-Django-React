# test_paginated_games.py oder test_consumers.py innerhalb Ihrer Django App
from channels.testing import WebsocketCommunicator
from django.test import TestCase
# from tictactoe.apps.core.routing import websocket_urlpatterns
#
#
# # Testklasse für den Chat-Consumer.
# class ChatConsumerTests(TestCase):
#     async def test_chat_consumer(self):
#         # Erstellen eines WebsocketCommunicator, der zum Testen Ihrer Consumer verwendet wird
#         communicator = WebsocketCommunicator(websocket_urlpatterns, "/ws/main-chat-socket/")
#         connected, subprotocol = await communicator.connect()
#         self.assertTrue(connected)
#
#         # Senden einer Nachricht an Ihren Consumer
#         await communicator.send_json_to({
#             'type': 'chat_message',
#             'message': 'Hello',
#             'sender': 'testuser',
#             'timestamp': '01.01.2024 00:00:00'
#         })
#
#         # Empfangen einer Antwort von Ihrem Consumer
#         response = await communicator.receive_json_from()
#         print(response)  # Sie können hier prüfen, was zurückgesendet wird
#
#         # Verbindung trennen
#         await communicator.disconnect()
#
#     def test_sync_helper(self):
#         # Dieses Beispiel zeigt, wie man asynchrone Tests in synchronem Code aufruft
#         import asgiref.sync
#         asgiref.sync.sync_to_async(self.test_chat_consumer)()


from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.api.models import PlayedGame
from unittest.mock import patch


class PaginateGamesTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123'
        )
        cls.game_win = PlayedGame.objects.create(player_x=cls.user, player_o=cls.user, winner=cls.user,
                                                 is_finished=True)
        cls.game_lose = PlayedGame.objects.create(player_x=cls.user, player_o=cls.user, winner=None, is_finished=True)
        cls.game_draw = PlayedGame.objects.create(player_x=cls.user, player_o=cls.user, winner=None, is_finished=False)

    def setUp(self):
        self.client.login(username='testuser', password='password123')

    def test_home_view(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_paginate_games_win_filter(self):
        response = self.client.get(reverse('core:paginate_games'), {'filter': 'win', 'sort': 'desc', 'page': 1})
        self.assertEqual(response.status_code, 200)
        self.assertIn('table_html', response.json())
        self.assertIn('has_next', response.json())
        self.assertIn('has_previous', response.json())
        self.assertIn('current_page', response.json())
        self.assertIn('total_pages', response.json())

    def test_paginate_games_lose_filter(self):
        response = self.client.get(reverse('core:paginate_games'), {'filter': 'lose', 'sort': 'asc', 'page': 1})
        self.assertEqual(response.status_code, 200)
        self.assertIn('table_html', response.json())

    def test_paginate_games_invalid_filter(self):
        response = self.client.get(reverse('core:paginate_games'), {'filter': 'invalid', 'sort': 'desc', 'page': 1})
        self.assertEqual(response.status_code, 200)
        self.assertIn('table_html', response.json())

    def test_paginate_games_valid_sort(self):
        response = self.client.get(reverse('core:paginate_games'), {'filter': 'all', 'sort': 'asc', 'page': 1})
        self.assertEqual(response.status_code, 200)
        self.assertIn('table_html', response.json())

    def test_paginate_games_invalid_sort(self):
        response = self.client.get(reverse('core:paginate_games'), {'filter': 'all', 'sort': 'invalid', 'page': 1})
        self.assertEqual(response.status_code, 200)
        self.assertIn('table_html', response.json())

    def test_paginate_games_no_results(self):
        PlayedGame.objects.all().delete()
        response = self.client.get(reverse('core:paginate_games'), {'filter': 'all', 'sort': 'desc', 'page': 1})

        self.assertEqual(response.status_code, 200)
        self.assertIn('table_html', response.json())

        actual_html = '\n'.join(line.strip() for line in response.json()['table_html'].splitlines())

        expected_html = '''<tr>
        <td colspan="5">No games found.</td>
    </tr>'''

        # Compare the normalized HTML
        self.assertEqual(actual_html, expected_html)

    @patch('apps.core.views.get_game_filter')
    def test_get_game_filter_error(self, mock_get_game_filter):
        mock_get_game_filter.side_effect = Exception("Database Error")
        response = self.client.get(reverse('core:paginate_games'), {'filter': 'win', 'sort': 'asc', 'page': 1})
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.json())

    @patch('apps.core.views.get_sorted_games')
    def test_get_sorted_games_error(self, mock_get_sorted_games):
        mock_get_sorted_games.side_effect = Exception("Sorting Error")
        response = self.client.get(reverse('core:paginate_games'), {'filter': 'win', 'sort': 'asc', 'page': 1})
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.json())

    @patch('apps.core.views.get_paginated_games')
    def test_get_paginated_games_error(self, mock_get_paginated_games):
        mock_get_paginated_games.side_effect = Exception("Pagination Error")
        response = self.client.get(reverse('core:paginate_games'), {'filter': 'win', 'sort': 'asc', 'page': 1})
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.json())
