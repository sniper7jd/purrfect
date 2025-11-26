"""
Django settings for PetConnect project.
Instagram-like social platform for pets.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-this-in-production')
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = [
    "petconnect-2gip.onrender.com",
    ".onrender.com",
    "localhost",
    "127.0.0.1",
]

# Application definition
INSTALLED_APPS = [
    'daphne',  # ASGI server for WebSockets
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Third-party apps
    'channels',
    'crispy_forms',
    'crispy_tailwind',
    
    # Local apps
    'accounts.apps.AccountsConfig',
    'pets.apps.PetsConfig',
    'feed.apps.FeedConfig',
    'chat.apps.ChatConfig',
    'playdates.apps.PlaydatesConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'petconnect.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'petconnect.context_processors.global_settings',
            ],
        },
    },
]

# ASGI for WebSocket support
ASGI_APPLICATION = 'petconnect.asgi.application'
WSGI_APPLICATION = 'petconnect.wsgi.application'

# Channel layers for WebSocket
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
        # For production, use Redis:
        # 'BACKEND': 'channels_redis.core.RedisChannelLayer',
        # 'CONFIG': {
        #     'hosts': [('127.0.0.1', 6379)],
        # },
    }
}

# Database - PostgreSQL
# Supports DATABASE_URL (used by Render, Heroku, etc.) or individual settings
import getpass
import dj_database_url

DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Production: Use DATABASE_URL from Render
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'petconnect'),
            'USER': os.environ.get('DB_USER', getpass.getuser()),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms with Tailwind
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# Login/Logout
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'feed:home'
LOGOUT_REDIRECT_URL = 'feed:home'

# Email
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('MAIL_SERVER', 'localhost')
EMAIL_PORT = int(os.environ.get('MAIL_PORT', 25))
EMAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('MAIL_USERNAME', '')
EMAIL_HOST_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@petconnect.com')

# API Keys
PLACES_API_KEY = os.environ.get('PLACES_API_KEY', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Pagination
POSTS_PER_PAGE = 10
PETS_PER_PAGE = 12

# Production Security Settings
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if host != 'localhost' and host != '127.0.0.1']

# WhiteNoise for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Create directories (only in development)
if DEBUG:
    (BASE_DIR / 'logs').mkdir(exist_ok=True)
    (BASE_DIR / 'media' / 'posts').mkdir(parents=True, exist_ok=True)
    (BASE_DIR / 'media' / 'stories').mkdir(parents=True, exist_ok=True)
    (BASE_DIR / 'media' / 'pets').mkdir(parents=True, exist_ok=True)
    (BASE_DIR / 'media' / 'profiles').mkdir(parents=True, exist_ok=True)

