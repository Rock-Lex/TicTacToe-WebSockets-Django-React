from django.db import models
from django.db.models import SET_DEFAULT
from apps.accounts.models import User
import string
import random


def generate_unique_code(length=6):
    while True:
        code = ''.join(random.choices(string.ascii_uppercase, k=length))
        if not GameRoom.objects.filter(code=code).exists():
            return code


class PlayedGame(models.Model):
    code = models.CharField(
        max_length=8,
        default=generate_unique_code,
        unique=True,
        help_text="Unique identifier for the played game."
    )
    winner = models.ForeignKey(
        User,
        related_name='games_won',
        on_delete=SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        help_text="The user who won the game."
    )
    player_x = models.ForeignKey(
        User,
        related_name='games_as_x',
        on_delete=SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        help_text="The user who played as X."
    )
    player_o = models.ForeignKey(
        User,
        related_name='games_as_o',
        on_delete=SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        help_text="The user who played as O."
    )
    is_finished = models.BooleanField(
        default=False,
        help_text="Whether the game has been completed."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the game was created."
    )

    class Meta:
        verbose_name = "Played Game"
        verbose_name_plural = "Played Games"

    def __str__(self):
        return f"PlayedGame {self.code} - Winner: {self.winner}"


class GameRoom(models.Model):
    code = models.CharField(
        max_length=8,
        default=generate_unique_code,
        unique=True,
        help_text="Unique identifier for the game room."
    )
    host = models.CharField(
        max_length=50,
        help_text="Session key of the host of the game room."
    )
    player_x = models.ForeignKey(
        User,
        related_name='active_games_as_x',
        on_delete=SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        help_text="The user playing as X in the room."
    )
    player_o = models.ForeignKey(
        User,
        related_name='active_games_as_o',
        on_delete=SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        help_text="The user playing as O in the room."
    )
    game_option = models.CharField(
        max_length=1,
        default="r",
        help_text="Game option: 'r' for random, 'x' for Player X, 'o' for Player O."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the room was created."
    )
    game_started = models.BooleanField(
        default=False,
        help_text="Whether the game has started."
    )

    class Meta:
        verbose_name = "Game Room"
        verbose_name_plural = "Game Rooms"

    def __str__(self):
        return f"GameRoom {self.code} - Host: {self.host}"