import json
import logging
import random

from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from datetime import timedelta
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from apps.api.models import User, GameRoom
from apps.utils.redis_client import redis_client

PLAYERS_SKILL_RANGE = 200

logger = logging.getLogger('tictactoe')


@shared_task
def delete_unused_gamerooms():
    """Delete game rooms that were created but not started within 12 hours."""
    try:
        twelve_hours_ago = timezone.now() - timedelta(hours=12)
        deleted_count, _ = GameRoom.objects.filter(game_started=False, created_at__lte=twelve_hours_ago).delete()
        logger.info(f"Deleted {deleted_count} unstarted game rooms older than 12 hours.")
    except Exception as e:
        logger.error(f"Failed to delete unused game rooms: {e}")


@shared_task
def process_queue(game_mode='1v1', skill_range=PLAYERS_SKILL_RANGE):
    """Process the player queue and match players based on skill range."""
    queue_key = f"game_queue_{game_mode}"

    try:
        while redis_client.zcard(queue_key) > 1:
            player_1_data, skill_score = _get_first_player_from_queue(queue_key)
            if not player_1_data:
                logger.info("No players found in the queue.")
                break

            player_2_member = _find_match(player_1_data['player_id'], skill_score, queue_key, skill_range)
            if player_2_member:
                player_2_data = json.loads(player_2_member)
                _create_game_room(player_1_data, player_2_data)
                redis_client.zrem(queue_key, json.dumps(player_1_data))
                redis_client.zrem(queue_key, player_2_member)
            else:
                logger.info(f"No match found for Player {player_1_data['player_id']}.")
                break
    except Exception as e:
        logger.error(f"Error processing queue: {e}")


def _get_first_player_from_queue(queue_key):
    try:
        players = redis_client.zrange(queue_key, 0, 0, withscores=True)
        if players:
            player_member, skill_score = players[0]
            return json.loads(player_member), skill_score
    except Exception as e:
        logger.error(f"Error retrieving first player from queue: {e}")
    return None, None


def _find_match(player_id, player_skill, queue_key, skill_range):
    try:
        candidates = redis_client.zrangebyscore(queue_key, player_skill - skill_range, player_skill + skill_range, withscores=True)
        for member, _ in candidates:
            candidate_data = json.loads(member)
            if candidate_data['player_id'] != player_id:
                return member
    except Exception as e:
        logger.error(f"Error finding match for Player {player_id}: {e}")
    return None


def _create_game_room(player_1_data, player_2_data):
    try:
        player_1_id, player_1_host = player_1_data['player_id'], player_1_data['host']
        player_2_id, player_2_host = player_2_data['player_id'], player_2_data['host']

        player_1_side = random.choice(['x', 'o'])
        player_x, player_o, host = _assign_roles(player_1_side, player_1_id, player_2_id, player_1_host, player_2_host)

        game_room = GameRoom(player_x=player_x, player_o=player_o, host=host, game_option='x')
        game_room.save()
        _notify_users(game_room)
    except ObjectDoesNotExist as e:
        logger.error(f"Error creating game room: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during game room creation: {e}")


def _assign_roles(player_1_side, player_1_id, player_2_id, player_1_host, player_2_host):
    try:
        if player_1_side == 'o':
            return (
                User.objects.get(pk=player_2_id),
                User.objects.get(pk=player_1_id),
                player_2_host
            )
        else:
            return (
                User.objects.get(pk=player_1_id),
                User.objects.get(pk=player_2_id),
                player_1_host
            )
    except ObjectDoesNotExist as e:
        logger.error(f"User assignment error: {e}")
        raise


def _notify_users(game_room):
    try:
        channel_layer = get_channel_layer()
        group_name_o = f"queue_member_{game_room.player_o.id}"
        group_name_x = f"queue_member_{game_room.player_x.id}"

        async_to_sync(channel_layer.group_send)(
            group_name_o,
            {'type': "match_found", 'gameRoomCode': game_room.code}
        )
        async_to_sync(channel_layer.group_send)(
            group_name_x,
            {'type': "match_found", 'gameRoomCode': game_room.code}
        )
    except Exception as e:
        logger.error(f"Error notifying users for game room {game_room.code}: {e}")