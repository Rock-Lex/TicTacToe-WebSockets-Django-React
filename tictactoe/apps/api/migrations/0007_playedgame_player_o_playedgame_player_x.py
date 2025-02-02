# Generated by Django 4.2.17 on 2024-12-26 18:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0006_alter_playedgame_winner'),
    ]

    operations = [
        migrations.AddField(
            model_name='playedgame',
            name='player_o',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='history_player_y', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='playedgame',
            name='player_x',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='history_player_x', to=settings.AUTH_USER_MODEL),
        ),
    ]
