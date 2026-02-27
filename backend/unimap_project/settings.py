"""
Django settings for unimap_project.

This file is configured to work with:
- Neon Postgres cloud database (for production/me)
- SQLite (for team members locally)
- python-decouple for secret management
- Whitenoise for static files in production
- REST framework


"""
from datetime import timedelta
from decouple import config
import os
from pathlib import Path

# BASE DIRECTORY
BASE_DIR = Path(__file__).resolve().parent.parent

CORS_ALLOW_ALL_ORIGINS = True

# SECURITY
SECRET_KEY = config("SECRET_KEY")

# ORS_KEY is for OpenRouteService API
ORS_KEY = config("ORS_KEY")

# DEBUG mode
DEBUG = config("DEBUG", default=False, cast=bool)

# Hosts allowed to serve the app
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'Uba-navigator.onrender.com']

# MEDIA (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# APPLICATIONS
INSTALLED_APPS = [
    # Third-party apps
    'rest_framework',
    'cloudinary',
    'cloudinary_storage',
    
    # Your apps
    'campus.apps.CampusConfig',
    
    #new apps still in development
    'accounts.apps.AccountsConfig', #currently working on account
    # 'academic.apps.AcademicConfig',
    # 'attendance.apps.AttendanceConfig',
    # 'associate.apps.AssociateConfig',
        
        
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
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'campus.middleware.SiteVisitMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# REST Framework & JWT
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

# URLS & TEMPLATES
ROOT_URLCONF = 'unimap_project.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'unimap_project.wsgi.application'


# ==================== DATABASE CONFIGURATION ====================
# This works for BOTH:
# - me in production (Neon PostgreSQL) - Just set USE_SQLITE=False in your .env
# - Team (SQLite) - Just set USE_SQLITE=True in their .env
# ================================================================

USE_SQLITE = config('USE_SQLITE', default=False, cast=bool)

if USE_SQLITE:
    # Team members use SQLite locally
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # You use Neon PostgreSQL (or any PostgreSQL)
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
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# DEFAULT AUTO FIELD
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CLOUDINARY MEDIA STORAGE
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': config('CLOUDINARY_API_KEY'),
    'API_SECRET': config('CLOUDINARY_API_SECRET'),
}