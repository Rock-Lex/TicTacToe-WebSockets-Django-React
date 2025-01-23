import json
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from selenium.webdriver.remote.utils import load_json

from apps.api.models import *
from apps.api.views import get_user_from_jwt_token
from apps.utils.redis_client import (REDIS_CHAT_EXPIRATION_SECONDS,
                                     REDIS_GAMECHAT_EXPIRATION_SECONDS,
                                     REDIS_CHAT_MESSAGES_LIST,
                                     redis_client)
from apps.utils.redis_utils import (set_redis_expiation,
                                    add_user_to_queue,
                                    delete_user_from_queue,
                                    fetch_redis_list,
                                    store_message_in_redis_list)
from apps.utils.utils import get_current_timestamp


logger = logging.getLogger("tictactoe")

class ChatConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.room_group_name = 'main_chat'

    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        self.user = self.scope.get('user')

        self._send_connection_established_message()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            logger.warning("Received empty text_data.")
            return

        logger.info(f"Received data: {text_data}")
        try:
            text_data_json = json.loads(text_data)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            return

        message_type = text_data_json.get('type')
        if message_type == 'latest_messages_request':
            self._send_recent_messages()
        elif message_type == 'chat_message':
            self._handle_chat_message(text_data_json)
        else:
            logger.warning(f"Unsupported message type: {message_type}")

    def chat_message(self, event):
        self.send(text_data=json.dumps({
            'type': 'chat',
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event.get('timestamp', '')
        }))

    def _send_connection_established_message(self):
        self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'You are now connected!',
        }))

    def _handle_chat_message(self, text_data_json):
        message = text_data_json.get('message', '')
        if not message:
            logger.warning("Received empty message content.")
            return

        sender_username = self.user.username if self.user and self.user.is_authenticated else 'Anonymous'
        timestamp = get_current_timestamp()

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender_username,
                'timestamp': timestamp
            }
        )
        store_message_in_redis_list(
            list_name=REDIS_CHAT_MESSAGES_LIST,
            message=message,
            sender=sender_username,
            timestamp=timestamp
        )

    def _send_recent_messages(self):
        recent_messages = fetch_redis_list(REDIS_CHAT_MESSAGES_LIST)
        for message in recent_messages:
            self.send(text_data=json.dumps({
                'type': 'chat',
                'message': message['message'],
                'sender': message['sender'],
                'timestamp': message['timestamp'],
            }))

class GameRoomChatConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.room_code = None
        self.room_group_name = None

    def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f"chat_room_{self.room_code}"

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        self.user = self.scope.get('user')

        self._send_connection_established_message()

        set_redis_expiation(f'recent_messages_{self.room_code}', REDIS_GAMECHAT_EXPIRATION_SECONDS)

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            logger.warning("Received empty text_data.")
            return

        logger.info(f"Received data: {text_data}")
        try:
            text_data_json = json.loads(text_data)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            return

        message_type = text_data_json.get('type')
        if message_type == 'latest_messages_request':
            self._send_recent_messages()
        elif message_type == 'chat':
            self._handle_chat_message(text_data_json)
        else:
            logger.warning(f"Unsupported message type: {message_type}")

    def chat_message(self, event):
        self.send(text_data=json.dumps({
            'type': 'chat',
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event.get('timestamp', '')
        }))

    def _send_connection_established_message(self):
        self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f"You are now connected to chat room {self.room_group_name}!",
        }))

    def _handle_chat_message(self, text_data_json):
        message = text_data_json.get('message', '')
        if not message:
            logger.warning("Received empty message content.")
            return

        sender_username = self.user.username if self.user and self.user.is_authenticated else 'Anonymous'
        timestamp = get_current_timestamp()

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender_username,
                'timestamp': timestamp
            }
        )
        store_message_in_redis_list(
            list_name=f'recent_messages_{self.room_code}',
            message=message,
            sender=sender_username,
            timestamp=timestamp
        )

    def _send_recent_messages(self):
        recent_messages = fetch_redis_list(f'recent_messages_{self.room_code}')
        for message in recent_messages:
            self.send(text_data=json.dumps({
                'type': 'chat',
                'message': message['message'],
                'sender': message['sender'],
                'timestamp': message['timestamp'],
            }))


class SearchQueueConsumer(WebsocketConsumer):
    def connect(self):
        jwt_token = self.scope['url_route']['kwargs']['jwt_token']
        host_code = self.scope['url_route']['kwargs']['host_code']

        self._initialize_user(jwt_token)
        self._add_to_group()
        self._add_user_to_queue(host_code)
        self._send_connection_message()

    def disconnect(self, code):
        self._remove_from_group()
        self._remove_user_from_queue()

    def match_found(self, event):
        self._notify_match_found(event)

    def _initialize_user(self, jwt_token):
        try:
            self.user = get_user_from_jwt_token(jwt_token)
            self.room_group_name = f'queue_member_{self.user.id}'
        except Exception as e:
            logger.error(f"Error initializing user: {e}")
            self.close()

    def _add_to_group(self):
        try:
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )
            self.accept()
        except Exception as e:
            logger.error(f"Error adding to group: {e}")
            self.close()

    def _add_user_to_queue(self, host_code):
        try:
            add_user_to_queue(player_id=self.user.id, skill_rating=self.user.skill_rating, host=host_code)
        except Exception as e:
            logger.error(f"Error adding user to queue: {e}")
            self.close()

    def _send_connection_message(self):
        try:
            self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'You are now connected!',
            }))
        except Exception as e:
            logger.error(f"Error sending connection message: {e}")

    def _remove_from_group(self):
        try:
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )
        except Exception as e:
            logger.error(f"Error removing from group: {e}")

    def _remove_user_from_queue(self):
        try:
            delete_user_from_queue(
                player_id=self.user.id,
                host=self.scope['url_route']['kwargs']['host_code']
            )
        except Exception as e:
            logger.error(f"Error removing user from queue: {e}")

    def _notify_match_found(self, event):
        try:
            game_room_code = event['gameRoomCode']
            self.send(text_data=json.dumps({
                'type': 'match_found',
                'gameRoomCode': game_room_code,
            }))
        except Exception as e:
            logger.error(f"Error notifying match found: {e}")


class GameRoomConsumer(WebsocketConsumer):
    """ Public """
    def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f'game_room_{self.room_code}'

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

        self._send_connection_established()

        set_redis_expiation(f"ready_{self.room_code}", 3600)
        set_redis_expiation(f"latest_gamestate_{self.room_code}", 3600)

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = self._load_json_with_error_handling(text_data)
        match text_data_json['type']:

            case 'game_state':
                self._handle_game_state(text_data_json)

            case'time_win':
                self._handle_time_win(text_data_json)

            case 'game_started':
                self._handle_game_start(text_data_json)

            case 'ready':
                self._handle_ready_status(text_data_json)

            case 'latest_gamestate_request':
                self._handle_latest_gamestate()

            case 'acknowledgement':
                self._broadcast_acknowledgement(text_data_json)

            case _:
                logger.warning(f"Unknown message type: {text_data_json['type']}")

    def acknowledgement(self, event):
        player_x = event['player_x']
        player_o = event['player_o']

        self.send(text_data=json.dumps({
            'type': 'acknowledgement',
            'player_x': player_x,
            'player_o': player_o
        }))

    def ready(self, event):
        try:
            player_type = event.get("player_type")
            if not player_type:
                logger.error("Missing player_type in ready event.")
                return

            self.send(text_data=json.dumps({
                'type': f'ready_{player_type}',
                f'isReadyPlayer_{player_type}': True,
            }))
        except Exception as e:
            logger.error(f"Error sending ready signal: {e}", exc_info=True)

    def game_state_message(self, event):
        try:
            game_state = {
                'type': 'game_state',
                'squares': event.get('squares'),
                'winner': event.get('winner'),
                'player_x': event.get('player_x'),
                'player_o': event.get('player_o'),
                'xIsNext': event.get('xIsNext'),
            }

            self.send(text_data=json.dumps(game_state))
        except ValueError as ve:
            logger.error(f"Validation error in game_state_message: {ve}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error in game_state_message: {e}", exc_info=True)


    """ Private """
    def _handle_game_state(self, text_data_json):
        try:
            logger.debug(text_data_json)
            squares = text_data_json['squares']
            winner = self.calculate_winner(squares)

            if winner:
                player_x_inst, player_o_inst = self._get_players_instances(text_data_json)
                if not player_x_inst or not player_o_inst:
                    logger.error("Failed to retrieve player instances. Aborting game state processing.")
                    return

                winner, loser = self._found_winner_and_loser_via_winner_type(player_x_inst, player_o_inst, winner)
                self._process_players_skill_ratings(winner, loser)
                self._process_played_game(room_code=self.room_code,
                                          winner=winner,
                                          player_x_inst=player_x_inst,
                                          player_o_inst=player_o_inst)

                winner = winner.username
            else:
                logger.info("No winner yet. Continuing game.")

            self._send_gamestate(winner=winner, data=text_data_json)
            self._store_latest_gamestate_in_redis(squares, text_data_json)
        except KeyError as e:
            logger.error(f"Missing key in game state data: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error handling game state: {e}", exc_info=True)

    def _handle_time_win(self, text_data_json):
        try:
            winner_username = text_data_json.get('winner')
            if not winner_username:
                logger.error("Winner username not provided in time win event.")
                return

            player_x_inst, player_o_inst = self._get_players_instances(text_data_json)
            if not player_x_inst or not player_o_inst:
                logger.error("Failed to retrieve player instances for time win. Aborting.")
                return

            winner, loser = self._found_winner_and_loser(player_x_inst, player_o_inst, winner_username)

            self._process_players_skill_ratings(winner, loser)
            self._process_played_game(room_code=self.room_code,
                                      winner=winner,
                                      player_x_inst=player_x_inst,
                                      player_o_inst=player_o_inst)

            self._store_latest_gamestate_in_redis(text_data_json['squares'], text_data_json)
            self._send_gamestate(winner=winner.username, data=text_data_json)
        except KeyError as e:
            logger.error(f"Missing key in time win data: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error handling time win: {e}", exc_info=True)



    def _handle_game_start(self, text_data_json):
        if not PlayedGame.objects.filter(code=self.room_code).exists():
            player_x = User.objects.get(username=text_data_json.get('player_x', None))
            player_o = User.objects.get(username=text_data_json.get('player_o', None))

            played_game = PlayedGame(code=self.room_code,
                                     player_x=player_x,
                                     player_o=player_o)
            try:
                played_game.save()
            except IntegrityError as e:
                logger.error(f"Error saving played game: {played_game} : {e}")
        else:
            logger.warning(f"Game already started: {self.room_code}")

    def _handle_ready_status(self, text_data_json):
        is_ready_player_x = text_data_json.get('isReadyPlayer_x', None)
        is_ready_player_o = text_data_json.get('isReadyPlayer_o', None)

        if is_ready_player_x:
            self._broadcast_ready_player('x')
            self._store_ready_status_in_redis({'isReadyPlayer_x': True})
        if is_ready_player_o:
            self._broadcast_ready_player('o')
            self._store_ready_status_in_redis({'isReadyPlayer_o': True})

    def _handle_latest_gamestate(self):
        self._send_ready_status_if_exists()
        self._send_latest_gamestate_if_exists()

    def _broadcast_acknowledgement(self, text_data_json):
        try:
            if not isinstance(text_data_json, dict):
                logger.error("Invalid data format. Expected a dictionary.")
                return

            player_x = text_data_json.get('player_x', None) # None is allowed. -> no check
            player_o = text_data_json.get('player_o', None) # None is allowed. -> no check

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'acknowledgement',
                    'player_x': player_x,
                    'player_o': player_o,
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting acknowledgement: {e}", exc_info=True)

    def _broadcast_ready_player(self, player_type):
        try:
            if not player_type:
                logger.error("Player type is required for broadcasting readiness.")
                return

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'ready',
                    'player_type': player_type,
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting ready status for player {player_type}: {e}", exc_info=True)

    def _send_ready_status_if_exists(self):
        try:
            latest_ready_state = redis_client.get(f'ready_{self.room_code}')
        except Exception as e:
            logger.error(f"Error getting ready state from Redis: {e}")
            return

        if latest_ready_state:
            ready_state = self._load_json_with_error_handling(latest_ready_state)
            if ready_state['isReadyPlayer_o'] is True:
                self._send_ready_player('o')
            if ready_state['isReadyPlayer_x'] is True:
                self._send_ready_player('x')

    def _send_ready_player(self, player_type):
        if not player_type:
            logger.error(f"No player type was passed : {player_type}") # Player type 'x' or 'o'
        self.send(text_data=json.dumps({
            'type': f'ready_{player_type}',
            f'isReadyPlayer_{player_type}': True,
        }))

    def _store_ready_status_in_redis(self, status_dict): # TODO
        key = f'ready_{self.room_code}'
        existing_state = redis_client.get(key)

        if existing_state:
            ready_state = self._load_json_with_error_handling(existing_state)
        else:
            ready_state = {
                'isReadyPlayer_o': None,
                'isReadyPlayer_x': None
            }
        ready_state.update(status_dict)

        redis_client.set(key, json.dumps(ready_state))

    def _store_latest_gamestate_in_redis(self, squares, data):
        try:
            x_is_next = data.get('xIsNext')
            if x_is_next is None:
                logger.warning(f"xIsNext was not provided or is invalid in data: {data}")

            redis_payload = {
                'type': 'game_state_message',
                'squares': squares,
                'xIsNext': x_is_next,
            }

            redis_client.set(f'latest_gamestate_{self.room_code}', json.dumps(redis_payload))
            logger.info(f"Game state stored in Redis for room {self.room_code}: {redis_payload}")

        except Exception as e:
            logger.error(f"Failed to store game state in Redis for room {self.room_code}: {e}", exc_info=True)

    def _send_latest_gamestate_if_exists(self):
        latest_gamestate = redis_client.get(f"latest_gamestate_{self.room_code}")
        if latest_gamestate:
            game_state = json.loads(latest_gamestate)
            logger.info(game_state)
            self.send(text_data=json.dumps({
                'type': 'latest_gamestate',
                'squares': game_state['squares'],
                'xIsNext': game_state['xIsNext'],
            }))

    def _send_connection_established(self):
        self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'You are now connected!',
        }))


    """ Utils"""
    @staticmethod
    def _get_player_instance_from_username(username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            logger.error(f"User with username '{username}' does not exist.")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving user '{username}': {e}", exc_info=True)
            return None

    @staticmethod
    def _found_winner_and_loser(player_x_inst, player_o_inst, winner):
        logger.debug(f"Found winner: {winner}")
        logger.debug(f"Found player_x_inst: {player_x_inst.username}")
        logger.debug(f"Found player_o_inst: {player_o_inst.username}")
        if winner == player_x_inst.username:
            winner = player_x_inst
            loser = player_o_inst

        elif winner == player_o_inst.username:
            winner = player_o_inst
            loser = player_x_inst
        else:
            logger.error("Invalid winner")
            return None, None

        return winner, loser

    @staticmethod
    def _found_winner_and_loser_via_winner_type(player_x_inst, player_o_inst, winner_type):
        if winner_type == 'X':
            winner = player_x_inst
            loser = player_o_inst
        elif winner_type == 'O':
            winner = player_o_inst
            loser = player_x_inst
        else:
            logger.error("Invalid winner type")
            return None, None

        return winner, loser

    @staticmethod
    def _process_players_skill_ratings(winner, loser):
        # TODO: Implement players ratings
        logger.warning("NOT IMPLEMENTED")

    @staticmethod
    def _delete_gameroom(room_code):
        try:
            GameRoom.objects.filter(code=room_code).delete()
            logger.info(f"Successfully deleted GameRoom with code {room_code}")
        except Exception as e:
            logger.error(f"Failed to delete GameRoom with code {room_code}: {e}", exc_info=True)

    @staticmethod
    def calculate_winner(squares):
        winning_combination = [
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],
            [0, 3, 6],
            [1, 4, 7],
            [2, 5, 8],
            [0, 4, 8],
            [2, 4, 6]
        ]

        for combination in winning_combination:
            a, b, c = combination
            if squares[a] and squares[a] == squares[b] and squares[a] == squares[c]:
                return squares[a]

        return None

    def _get_players_instances(self, text_data_json):
        try:
            player_x_username = text_data_json.get('player_x')
            player_o_username = text_data_json.get('player_o')

            if not player_x_username or not player_o_username:
                raise ValueError("Both player_x and player_o usernames are required.")

            player_x_inst = self._get_player_instance_from_username(player_x_username)
            player_o_inst = self._get_player_instance_from_username(player_o_username)

            return player_x_inst, player_o_inst
        except ValueError as ve:
            logger.error(f"Validation error: {ve}", exc_info=True)
            return None, None
        except Exception as e:
            logger.error(f"Error retrieving player instances: {e}", exc_info=True)
            return None, None

    def _process_played_game(self, room_code, winner, player_x_inst, player_o_inst):
        self._delete_gameroom(room_code)

        try:
            self._delete_gameroom(room_code)

            played_game = PlayedGame.objects.get(code=room_code)
            played_game.winner = winner
            played_game.player_x = player_x_inst
            played_game.player_o = player_o_inst
            played_game.is_finished = True
            played_game.save()

            logger.info(f"Successfully processed played game for room code {room_code}")
        except PlayedGame.DoesNotExist:
            logger.error(f"PlayedGame with room code {room_code} does not exist", exc_info=True)
        except Exception as e:
            logger.error(f"Error processing played game for room code {room_code}: {e}", exc_info=True)

    def _send_gamestate(self, winner, data):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'game_state_message',
                'squares': data.get('squares', None),
                'winner': winner,
                'player_x': data.get('player_x', None),
                'player_o': data.get('player_o', None),
                'xIsNext': data.get('xIsNext', None),
            }
        )


    def _load_json_with_error_handling(self, raw_data):
        try:
            return json.loads(raw_data)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {raw_data}. Error: {e}", exc_info=True)
            self.close(code=4000)
        except TypeError as e:
            logger.error(f"Expected a string for JSON decoding but got: {raw_data}. Error: {e}", exc_info=True)
            self.close(code=4001)
        return None


class GameRoomConsumerOld(WebsocketConsumer):
    def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f"room_{self.room_code}"

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

        self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'You are now connected!',
        }))
        redis_client.expire(f"ready_{self.room_code}", 3600)
        redis_client.expire(f"latest_gamestate_{self.room_code}", 3600)

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)

        if text_data_json['type'] == 'latest_gamestate_request':
            self.get_and_send_ready()
            self.get_and_send_latest_gamestate()

            return
        elif text_data_json['type'] == "acknowledgement":
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'acknowledgement',
                    'player_x': text_data_json.get('player_x', None),
                    'player_o': text_data_json.get('player_o', None)
                }

            )
            return
        elif text_data_json['type'] == "ready":
            is_ready_player_x = text_data_json.get('isReadyPlayer_x', None)
            is_ready_player_o = text_data_json.get('isReadyPlayer_o', None)

            if is_ready_player_x:
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'ready_x',
                        'isReadyPlayer_x': is_ready_player_x,
                    }

                )
                async_to_sync(self.channel_layer.group_send)(

                    self.room_group_name,
                    {
                        'type': 'store_ready',
                        'isReadyPlayer_x': is_ready_player_x,
                    }
                )
            else:
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'ready_o',
                        'isReadyPlayer_o': is_ready_player_o,
                    }
                )
                async_to_sync(self.channel_layer.group_send)(

                    self.room_group_name,
                    {
                        'type': 'store_ready',
                        'isReadyPlayer_o': is_ready_player_o,
                    }
                )
            return
        elif text_data_json['type'] == "game_started":
            if not PlayedGame.objects.filter(code=self.room_code).exists():
                player_x = User.objects.get(username=text_data_json.get('player_x', None))
                player_o = User.objects.get(username=text_data_json.get('player_o', None))

                played_game = PlayedGame(code=self.room_code,
                                         player_x=player_x,
                                         player_o=player_o)
                try:
                    played_game.save()
                except IntegrityError:
                    pass
            return
        elif text_data_json['type'] == "time_win":

            winner = text_data_json['winner']
            room_code = text_data_json['room_code']

            try:
                player_x_inst = User.objects.get(username=text_data_json.get('player_x', None))
                player_o_inst = User.objects.get(username=text_data_json.get('player_o', None))

                if winner == player_x_inst.username:
                    winner = player_x_inst
                    looser = player_o_inst

                elif winner == player_o_inst.username:
                    winner = player_o_inst
                    looser = player_x_inst

                GameRoom.objects.filter(code=room_code).delete()

                played_game = PlayedGame.objects.get(code=room_code)
                played_game.winner = winner
                played_game.player_x = player_x_inst
                played_game.player_o = player_o_inst
                played_game.is_finished = True
                played_game.save()

                # winner.skill_rating += 25 # TODO make a rating system
                # looser.skill_rating -= 25
                # winner.save()
                # looser.save()

                winner = winner.username
            except Exception as e:
                print(e)

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'game_state_message',
                    'squares': text_data_json.get('squares', None),
                    'winner': winner,
                    'player_x': text_data_json.get('player_x', None),
                    'player_o': text_data_json.get('player_o', None)
                }
            )
            return

        squares = text_data_json['squares']
        winner = self.calculate_winner(squares)

        if winner:
            room_code = text_data_json['room_code']
            try:
                GameRoom.objects.filter(code=room_code).delete()

                player_x_inst = User.objects.get(username=text_data_json.get('player_x', None))
                player_o_inst = User.objects.get(username=text_data_json.get('player_o', None))

                if winner == 'X':
                    winner = player_x_inst
                    looser = player_o_inst
                elif winner == 'O':
                    winner = player_o_inst
                    looser = player_x_inst

                played_game = PlayedGame.objects.get(code=room_code)
                played_game.winner = winner
                played_game.player_x = player_x_inst
                played_game.player_o = player_o_inst
                played_game.is_finished = True
                played_game.save()

                # winner.skill_rating += 25 # TODO make a rating system
                # looser.skill_rating -= 25
                # winner.save()
                # looser.save()

                winner = winner.username
            except Exception as e:
                print(e)

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'game_state_message',
                'squares': squares,
                'winner': winner,
                'player_x': text_data_json.get('player_x', None),
                'player_o': text_data_json.get('player_o', None),
                'xIsNext': text_data_json.get('xIsNext', None),
            }
        )

        async_to_sync(self.channel_layer.group_send)(

            self.room_group_name,
            {
                'type': 'store_game_state',
                'squares': squares,
                'xIsNext': text_data_json.get('xIsNext', None),
            }
        )

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def get_and_send_latest_gamestate(self):
        latest_gamestate = redis_client.get(f"latest_gamestate_{self.room_code}")
        if latest_gamestate:
            game_state = json.loads(latest_gamestate)
            self.send(text_data=json.dumps({
                'type': 'latest_gamestate',
                'squares': game_state['squares'],
                'xIsNext': game_state['xIsNext'],
            }))

    def get_and_send_ready(self):
        latest_ready_state = redis_client.get(f'ready_{self.room_code}')
        if latest_ready_state:
            ready_state = json.loads(latest_ready_state)
            if ready_state['isReadyPlayer_o'] is True:
                self.send(text_data=json.dumps({
                    'type': 'ready_o',
                    'isReadyPlayer_o': True,
                }))
            if ready_state['isReadyPlayer_x'] is True:
                self.send(text_data=json.dumps({
                    'type': 'ready_x',
                    'isReadyPlayer_x': True,
                }))

    def store_game_state(self, event):
        squares = event['squares']
        xIsNext = event['xIsNext']
        redis_client.set(f'latest_gamestate_{self.room_code}', json.dumps({
            'type': 'game_state_message',
            'squares': squares,
            'xIsNext': xIsNext,
        }))

    def store_ready(self, event):
        key = f'ready_{self.room_code}'
        existing_state = redis_client.get(key)

        if existing_state:
            ready_state = json.loads(existing_state)
        else:
            ready_state = {
                'isReadyPlayer_o': None,
                'isReadyPlayer_x': None
            }

        if 'isReadyPlayer_o' in event:
            ready_state['isReadyPlayer_o'] = event['isReadyPlayer_o']
        if 'isReadyPlayer_x' in event:
            ready_state['isReadyPlayer_x'] = event['isReadyPlayer_x']

        redis_client.set(key, json.dumps(ready_state))

    def game_state_message(self, event):
        squares = event['squares']
        winner = event['winner']
        player_x = event['player_x']
        player_o = event['player_o']
        xIsNext = event['xIsNext']

        self.send(text_data=json.dumps({
            'type': 'game_state',
            'squares': squares,
            'winner': winner,
            'player_x': player_x,
            'player_o': player_o,
            'xIsNext': xIsNext,
        }))

    def acknowledgement(self, event):
        player_x = event['player_x']
        player_o = event['player_o']

        self.send(text_data=json.dumps({
            'type': 'acknowledgement',
            'player_x': player_x,
            'player_o': player_o
        }))

    def ready_x(self, event):
        is_ready_player_x = event['isReadyPlayer_x']

        self.send(text_data=json.dumps({
            'type': 'ready_x',
            'isReadyPlayer_x': is_ready_player_x,
        }))

    def ready_o(self, event):
        is_ready_player_o = event['isReadyPlayer_o']

        self.send(text_data=json.dumps({
            'type': 'ready_o',
            'isReadyPlayer_o': is_ready_player_o,
        }))

    @staticmethod
    def calculate_winner(squares):
        lines = [
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],
            [0, 3, 6],
            [1, 4, 7],
            [2, 5, 8],
            [0, 4, 8],
            [2, 4, 6]
        ]

        for line in lines:
            a, b, c = line
            if squares[a] and squares[a] == squares[b] and squares[a] == squares[c]:
                return squares[a]

        return None
