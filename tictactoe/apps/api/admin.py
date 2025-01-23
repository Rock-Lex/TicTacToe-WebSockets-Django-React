from django.contrib import admin
from apps.api.models import GameRoom, PlayedGame


@admin.register(GameRoom)
class GameRoomAdmin(admin.ModelAdmin):
    """Admin interface for managing active game rooms."""
    list_display = ('code', 'host', 'player_x', 'player_o', 'game_option', 'game_started', 'created_at')
    list_filter = ('game_started', 'game_option', 'created_at')
    search_fields = ('code', 'host', 'player_x__username', 'player_o__username')
    ordering = ('-created_at',)
    readonly_fields = ('code', 'created_at')


@admin.register(PlayedGame)
class PlayedGameAdmin(admin.ModelAdmin):
    """Admin interface for managing played games."""
    list_display = ('code', 'winner', 'player_x', 'player_o', 'is_finished', 'created_at')
    list_filter = ('is_finished', 'created_at')
    search_fields = ('code', 'winner__username', 'player_x__username', 'player_o__username')
    ordering = ('-created_at',)
    readonly_fields = ('code', 'created_at')
