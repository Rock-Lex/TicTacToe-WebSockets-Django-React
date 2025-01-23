# Generated by Django 4.2.17 on 2024-12-26 17:29

import apps.api.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gameroom',
            name='code',
            field=models.CharField(default=apps.api.models.generate_unique_code, max_length=8, unique=True),
        ),
        migrations.AlterField(
            model_name='gameroom',
            name='game_option',
            field=models.CharField(default='r', max_length=1),
        ),
        migrations.CreateModel(
            name='PlayedGame',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default=apps.api.models.generate_unique_code, max_length=8, unique=True)),
                ('is_finished', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('winner', models.ForeignKey(default=0, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='winner', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
