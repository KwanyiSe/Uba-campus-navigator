"""
Django settings for unimap_project.

This file is configured to work with:
- Neon Postgres cloud database
- python-decouple for secret management
- Whitenoise for static files in production
- REST framework

Keep sensitive keys in a .env file in the project root.
"""

from decouple import config
import os
from pathlib import Path

# BASE DIRECTORY

# BASE_DIR is the root folder of the project, used for constructing paths
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY
# Keep the secret key secret! Stored in .env
SECRET_KEY = config("SECRET_KEY")

# ORS_KEY is for OpenRouteService API, stored in .env
ORS_KEY = config("ORS_KEY")

# DEBUG mode off in production
DEBUG = config("DEBUG", default=True, cast=bool)

# Hosts allowed to serve the app
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'Uba-navigator.onrender.com']

# MEDIA (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# APPLICATIONS
INSTALLED_APPS = [
    # Third-party apps
    'rest_framework',
    
    # Your apps
    'campus.apps.CampusConfig',
    
    # Default Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',         # Serve static files efficiently
    'django.contrib.sessions.middleware.SessionMiddleware', # Must run before custom tracking
    'campus.middleware.SiteVisitMiddleware',              # Custom visitor tracking
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# URLS & TEMPLATES

ROOT_URLCONF = 'unimap_project.urls'

# Templates for Django + admin
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',  # Required for admin
        'DIRS': [BASE_DIR / 'templates'],                               # Your templates folder
        'APP_DIRS': True,                                               # Enable app templates
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',          # Required by admin
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'unimap_project.wsgi.application'


# DATABASE
# Using Neon Postgres cloud database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config("DATABASE_NAME"),
        'USER': config("DATABASE_USER"),
        'PASSWORD': config("DATABASE_PASSWORD"),
        'HOST': config("DATABASE_HOST"),
        'PORT': config("DATABASE_PORT", cast=int),
        'OPTIONS': {
            'sslmode': config("DATABASE_SSLMODE", default="require"),
            'channel_binding': config("DB_CHANNEL_BINDING", default="require")
        },
    }
}

# PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# INTERNATIONALIZATION
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# STATIC FILES
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]  # For development
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')    # For production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# MEDIA
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# DEFAULT AUTO FIELD
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
