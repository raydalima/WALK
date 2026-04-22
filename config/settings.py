"""
Configurações do Django para o WALK.

O arquivo é único para desenvolvimento e produção. Em produção, configure
as variáveis de ambiente indicadas em .env.example.
"""

from pathlib import Path
from importlib.util import find_spec
import sys
from decouple import config, Csv
from django.core.exceptions import ImproperlyConfigured
from django.contrib.messages import constants as messages

def _parse_debug(value):
    normalized = str(value).strip().lower()
    if normalized in {'1', 'true', 'yes', 'on', 'debug'}:
        return True
    if normalized in {'0', 'false', 'no', 'off', 'release', 'prod', 'production'}:
        return False
    return bool(value)


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
DEFAULT_SECRET = (
    'django-insecure-CHANGE-THIS-'
    'IN-PRODUCTION-'
    '12345678'
)
SECRET_KEY = config('SECRET_KEY', default=DEFAULT_SECRET)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = _parse_debug(config('DEBUG', default='True'))

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1',
    cast=Csv()
)

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='',
    cast=Csv(),
)

if not DEBUG:
    if SECRET_KEY == DEFAULT_SECRET:
        raise ImproperlyConfigured(
            'Configure SECRET_KEY no ambiente antes de subir em produção.'
        )

# Application definition
WHITENOISE_AVAILABLE = find_spec('whitenoise') is not None

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps do projeto
    'accounts',
    'teachers',
    'courses',
    'students',
    'admin_panel.apps.AdminPanelConfig',
    'assessments.apps.AssessmentsConfig',
    'materials',
    'blog',
]

# Garante apps necessários para Questionários
if 'courses' not in INSTALLED_APPS:
    INSTALLED_APPS.append('courses')
if 'students' not in INSTALLED_APPS:
    INSTALLED_APPS.append('students')
if 'assessments' in INSTALLED_APPS:
    INSTALLED_APPS.remove('assessments')
if 'assessments.apps.AssessmentsConfig' not in INSTALLED_APPS:
    INSTALLED_APPS.append('assessments.apps.AssessmentsConfig')

# App de frequência (professores)
if (
    'attendance' not in INSTALLED_APPS
    and 'attendance.apps.AttendanceConfig' not in INSTALLED_APPS
):
    INSTALLED_APPS.append('attendance.apps.AttendanceConfig')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if WHITENOISE_AVAILABLE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

ROOT_URLCONF = 'config.urls'

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
                'django.template.context_processors.media',
                'students.context_processors.pre_registration_form',
            ],
        },
    },
]

WSGI_APPLICATION = 'walk.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

USE_SQLITE = config('USE_SQLITE', default=DEBUG, cast=bool)

if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Para produção com PostgreSQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
            'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=60, cast=int),
            'OPTIONS': {
                'connect_timeout': config(
                    'DB_CONNECT_TIMEOUT',
                    default=10,
                    cast=int,
                ),
            },
        }
    }

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'UserAttributeSimilarityValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'MinimumLengthValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'CommonPasswordValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'NumericPasswordValidator'
        ),
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
WHITENOISE_AUTOREFRESH = DEBUG
WHITENOISE_USE_FINDERS = DEBUG

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': (
            'whitenoise.storage.CompressedManifestStaticFilesStorage'
            if not DEBUG and WHITENOISE_AVAILABLE
            else 'django.contrib.staticfiles.storage.StaticFilesStorage'
        ),
    },
}

# Media files (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if 'test' in sys.argv:
    DEBUG = True
    # O histórico de migrações locais contém merges antigos inconsistentes.
    # Nos testes usamos o schema direto a partir dos models para validar a app.
    MIGRATION_MODULES = {
        'accounts': None,
        'admin_panel': None,
        'assessments': None,
        'attendance': None,
        'blog': None,
        'courses': None,
        'materials': None,
        'students': None,
        'teachers': None,
    }

# Login URLs
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard_redirect'
LOGOUT_REDIRECT_URL = 'accounts:login'

# Messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Email
# Em desenvolvimento, o console backend evita falhas quando ainda não há SMTP.
# Em produção, configure EMAIL_BACKEND/SMTP por variáveis de ambiente.
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default=(
        'django.core.mail.backends.console.EmailBackend'
        if DEBUG else 'django.core.mail.backends.smtp.EmailBackend'
    ),
)
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default='Cursinho Popular <nao-responda@localhost>',
)

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10 MB

# Security Settings for Production
if not DEBUG:
    SECURE_SSL_REDIRECT = config(
        'SECURE_SSL_REDIRECT',
        default=True,
        cast=bool,
    )
    if config('SECURE_PROXY_SSL_HEADER', default=True, cast=bool):
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_REFERRER_POLICY = 'same-origin'
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = False
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'
    SECURE_HSTS_SECONDS = config(
        'SECURE_HSTS_SECONDS',
        default=31536000,
        cast=int,
    )
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
        'SECURE_HSTS_INCLUDE_SUBDOMAINS',
        default=True,
        cast=bool,
    )
    SECURE_HSTS_PRELOAD = config(
        'SECURE_HSTS_PRELOAD',
        default=True,
        cast=bool,
    )
