from rest_framework import serializers
from .models import GameRoom


class GameRoomSerializer(serializers.ModelSerializer):
    player_x_username = serializers.SerializerMethodField()
    player_o_username = serializers.SerializerMethodField()

    class Meta:
        model = GameRoom
        fields = (
            'id',
            'code',
            'host',
            'player_x_username',
            'player_o_username',
            'game_option',
            'created_at'
        )

    def get_player_x_username(self, obj):
        return obj.player_x.username if obj.player_x else None

    def get_player_o_username(self, obj):
        return obj.player_o.username if obj.player_o else None


class CreateGameRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameRoom
        fields = ['game_option', 'player_x', 'player_o']

    def validate(self, data):
        if data.get('player_x') and data.get('player_o') and data['player_x'] == data['player_o']:
            raise serializers.ValidationError("Player X and Player O cannot be the same user.")
        return data