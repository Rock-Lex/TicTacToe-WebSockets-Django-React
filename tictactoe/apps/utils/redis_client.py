"""
Singleton redis client
"""

import redis
from django.conf import settings
from redis.exceptions import ConnectionError


REDIS_CHAT_EXPIRATION_SECONDS = 3600 # 1 hour
REDIS_GAMECHAT_EXPIRATION_SECONDS = 1800 # 30 minutes
REDIS_CHAT_MESSAGES_LIST = "recent_messages"

class RedisClient:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            try:
                cls._instance = redis.StrictRedis(**settings.REDIS_CONFIG)
                cls._instance.ping()
            except ConnectionError as e:
                raise ConnectionError("Unable to connect to Redis server.") from e
        return cls._instance

redis_client = RedisClient.get_instance()
redis_client.expire('recent_messages', REDIS_CHAT_EXPIRATION_SECONDS)