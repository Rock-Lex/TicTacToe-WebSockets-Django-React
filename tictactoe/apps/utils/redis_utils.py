import json
import logging

from apps.utils.redis_client import redis_client

logger = logging.getLogger(__name__)

"""
Client Settings
"""

def set_redis_expiation(list, time=3600):
    redis_client.expire(list, time)

"""
Helper functions
"""
def _generate_queue_key(game_mode='1v1'):
    return f"game_queue_{game_mode}"

def _generate_member(player_id, host):
    return json.dumps({'player_id': player_id, 'host': host})

"""
Search Queue Logic
"""

def add_user_to_queue(player_id, skill_rating, host, game_mode='1v1'):
    queue_key = _generate_queue_key(game_mode)
    member = _generate_member(player_id, host)
    redis_client.zadd(queue_key, {member: skill_rating})

def delete_user_from_queue(player_id, host, game_mode='1v1'):
    queue_key = _generate_queue_key(game_mode)
    member = _generate_member(player_id, host)
    redis_client.zrem(queue_key, member)


"""
MainChat and GameChat Messages Logic
"""
def fetch_redis_list(list_name):
    try:
        messages = redis_client.lrange(list_name, 0, -1)
        return [json.loads(message) for message in messages]
    except Exception as e:
        logger.error(f"Error retrieving messages from Redis: {e}")
        return []

def store_message_in_redis_list(list_name, message, sender, timestamp):
        try:
            redis_client.rpush(list_name, json.dumps({
                'type': 'chat',
                'message': message,
                'sender': sender,
                'timestamp': timestamp
            }))
        except Exception as e:
            logger.error(f"Error storing message in Redis {list_name}: {e}")
