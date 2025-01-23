import logging

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed


logger = logging.getLogger("tictactoe")


def get_user_from_jwt_token(token):
    jwt_auth = JWTAuthentication()
    try:
        validated_token = jwt_auth.get_validated_token(token)
        return jwt_auth.get_user(validated_token)
    except InvalidToken:
        logger.error("Invalid JWT token provided")
        raise AuthenticationFailed("Invalid token")
    except Exception as e:
        logger.error(f"Error validating JWT token: {e}")
        raise AuthenticationFailed(str(e))
