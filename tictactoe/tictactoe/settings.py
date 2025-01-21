from django.core.management.utils import get_random_secret_key
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
from colorlog import ColoredFormatter

import os


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', get_random_secret_key())

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False") == "True"
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "False") == "True"

ALLOWED_HOSTS = [f'{os.getenv('ALLOWED_HOSTS', 'localhost')}']

"""
CORS
"""
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv('CORS_ALLOWED_ORIGINS', '').split(',') if origin.strip()]
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True


"""
Apps
"""

INSTALLED_APPS = [
    'channels',
    'daphne',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'bootstrap5',
    'django_celery_beat',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'apps.accounts',
    'apps.core',
    'apps.frontend',
    'apps.api',
]


"""
Application definition
"""
ASGI_APPLICATION = 'tictactoe.asgi.application'
WSGI_APPLICATION = 'tictactoe.wsgi.application'


"""
Chanels configuration
"""
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [f'redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}']
        },
    },
}


"""
Celery configuration
"""
CELERY_BROKER_URL = f'redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/{os.getenv('REDIS_DB')}'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = f'redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/{os.getenv('REDIS_DB')}'

CELERY_BEAT_SCHEDULE = {
    'delete_unused_gamerooms_every_2_hours': {
        'task': 'apps.api.tasks.delete_unused_gamerooms',
        'schedule': 7200.0,  # 7200 seconds = 2 hours
    },
    'process_game_queue_every_5_seconds': {
        'task': 'apps.api.tasks.process_queue',
        'schedule': 5.0,
        'args': ('1v1', 50),
    },
}

if DEBUG:
    CELERY_BEAT_SCHEDULE['delete_unused_gamerooms_every_2_hours']['schedule'] = 30.0 # 30 seconds

"""
Redis configuration
"""
REDIS_CONFIG = {
    'host': f'{os.getenv('REDIS_HOST')}',
    'port': f'{os.getenv('REDIS_PORT')}',
    'db': f'{os.getenv('REDIS_DB')}',
    'decode_responses': True,
}


"""
Logging configuration
"""
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'color': {
            '()': 'colorlog.ColoredFormatter',
            'format': '%(log_color)s[%(levelname)s] %(message)s',
            'log_colors': {
                'DEBUG': 'blue',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            },
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'color',
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'error.log'),
        },
    },
    'loggers': {
        'tictactoe': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}


"""
Middleware configuration
"""
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.common.CommonMiddleware',

    'corsheaders.middleware.CorsMiddleware',
    'tictactoe.middleware.JWTAuthenticationMiddleware',
]


"""
URL and Templates configuration
"""
ROOT_URLCONF = 'tictactoe.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


"""
DB configuration
"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


"""
Auth configuration
"""
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTH_USER_MODEL = 'accounts.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=30),
}
JWT_ALGORITHM = 'HS512'

LOGIN_REDIRECT_URL = '/accounts/login/'

"""
Internationalization configuration
"""
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_TZ = True


"""
Static media (CSS, JavaScript, Images) configuration
"""
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    BASE_DIR / 'apps/frontend/static'
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

"""
Default primary key field type
"""
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

"""
Admin 
"""
ADMIN_URL = 'admin/'
