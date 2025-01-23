import random
import logging

from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from apps.utils.api_utils import get_user_from_jwt_token
from .serializers import GameRoomSerializer, CreateGameRoomSerializer
from .models import GameRoom

logger = logging.getLogger("tictactoe")


"""
API
"""
def get_tokens(request):
    if request.method == 'GET':
        csrf_token = request.COOKIES.get('csrftoken', '')
        jwt_token = request.session.get('jwt_token')
        if not jwt_token:
            return JsonResponse(
                {'jwt_token': '0', 'csrf_token': csrf_token, 'session_key': request.session.session_key})

        try:
            username = get_user_from_jwt_token(jwt_token).username
            return JsonResponse(
                {'jwt_token': jwt_token, 'csrf_token': csrf_token, 'session_key': request.session.session_key,
                 'username': username})
        except AuthenticationFailed as e:
            return JsonResponse({'error': str(e)}, status=401)


class GameRoomView(APIView):
    serializer_class = GameRoomSerializer

    def get(self, request):
        room_code = request.GET.get('gameRoomCode')
        if room_code:
            return self._get_game_room_by_code(room_code)
        return self._get_all_game_rooms()

    def post(self, request):
        serializer = CreateGameRoomSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)

        game_option = serializer.validated_data.get('game_option')
        host = self.request.session.session_key

        self._delete_existing_room(host)

        user = self._get_authenticated_user()
        if game_option == 'r':
            game_option = random.choice(['x', 'o'])

        game_room = self._create_game_room(game_option, host, user)
        return Response(GameRoomSerializer(game_room).data, status=status.HTTP_200_OK)

    def delete(self, request):
        game_room_code = request.GET.get('gameRoomCode')
        if not game_room_code:
            return JsonResponse({'error': 'Room code is required'}, status=400)

        try:
            game_room = GameRoom.objects.get(code=game_room_code)
        except ObjectDoesNotExist:
            logger.warning(f"Attempt to delete non-existent room with code {game_room_code}")
            return JsonResponse({'error': 'Room not found'}, status=404)

        if self._can_user_delete_room(request.user, game_room):
            game_room.delete()
            return JsonResponse({'success': 'Game cancelled successfully'})
        return JsonResponse({'error': 'User does not own the game'}, status=403)

    def _get_game_room_by_code(self, room_code):
        try:
            game_room = GameRoom.objects.get(code=room_code)
            data = GameRoomSerializer(game_room).data

            user = self._get_authenticated_user()
            if not user:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

            data['is_host'] = self.request.session.session_key == game_room.host
            data['room_exists'] = True

            if self._is_player_unauthorized(game_room, user):
                return Response({'error': 'Invalid Room Code', 'room_exists': False}, status=status.HTTP_404_NOT_FOUND)

            self._assign_user_to_room(game_room, user)
            self._add_player_data_to_response(data, game_room)

            return Response(data, status=status.HTTP_200_OK)
        except GameRoom.DoesNotExist:
            logger.warning(f"GameRoom with code {room_code} not found")
            return Response({'error': 'Invalid Room Code', 'room_exists': False}, status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def _get_all_game_rooms():
        games = GameRoom.objects.all()
        return JsonResponse(GameRoomSerializer(games, many=True).data, safe=False)

    @staticmethod
    def _delete_existing_room(host):
        existing_room = GameRoom.objects.filter(host=host).first()
        if existing_room:
            existing_room.delete()

    @staticmethod
    def _create_game_room(game_option, host, user):
        if game_option == 'o':
            return GameRoom.objects.create(host=host, game_option=game_option, player_o=user)
        if game_option == 'x':
            return GameRoom.objects.create(host=host, game_option=game_option, player_x=user)

    def _get_authenticated_user(self):
        jwt_token = self.request.session.get('jwt_token')
        if jwt_token:
            try:
                return get_user_from_jwt_token(jwt_token)
            except AuthenticationFailed:
                return None

    @staticmethod
    def _is_player_unauthorized(game_room, user):
        return (game_room.player_x and game_room.player_o and
                game_room.player_x != user and
                game_room.player_o != user)

    @staticmethod
    def _assign_user_to_room(game_room, user):
        if game_room.player_x is None and game_room.player_o != user:
            game_room.player_x = user
        elif game_room.player_o is None and game_room.player_x != user:
            game_room.player_o = user
        game_room.save()

    @staticmethod
    def _add_player_data_to_response(data, game_room):
        if game_room.player_x:
            data['player_x'] = game_room.player_x.username
        if game_room.player_o:
            data['player_o'] = game_room.player_o.username

    @staticmethod
    def _can_user_delete_room(user, game_room):
        return user == game_room.player_x or user == game_room.player_o