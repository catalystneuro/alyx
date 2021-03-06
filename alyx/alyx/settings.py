"""
Django settings for alyx project.

For more information on this file, see
https://docs.djangoproject.com/en/stable/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/stable/ref/settings/
"""

import os
from django.conf.locale.en import formats as en_formats
from decouple import config, Csv


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
try:
    from .settings_secret import *  # noqa
except ImportError:
    # We're probably autobuilding some documentation so let's just import something
    # to keep Django happy...
    from .settings_secret_template import *  # noqa

# Lab-specific settings
from .settings_lab import *  # noqa

en_formats.DATETIME_FORMAT = "d/m/Y H:i"
DATE_INPUT_FORMATS = ('%d/%m/%Y',)


if 'TRAVIS' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'travisci',
            'USER': 'postgres',
            'PASSWORD': '',
            'HOST': 'localhost',
            'PORT': '',
        }
    }


# Custom User model with UUID primary key
AUTH_USER_MODEL = 'misc.LabMember'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADED_PATH = os.path.dirname(BASE_DIR) + "/uploaded/"

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            '()': 'colorlog.ColoredFormatter',
            'format': '%(log_color)s%(asctime)s [%(levelname)s] ' +
                      '{%(filename)s:%(lineno)s} %(message)s',
            'datefmt': '%d/%m %H:%M:%S',
            'log_colors': {
                'DEBUG': 'cyan',
                'INFO': 'white',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            },
        }
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/alyx.log',
            'maxBytes': 16777216,
            'formatter': 'simple'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        }
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'WARNING',
        'propagate': True,
    }
}


if 'TRAVIS' in os.environ or 'READTHEDOCS' in os.environ:
    LOGGING['handlers']['file']['filename'] = 'alyx.log'


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!!
DEBUG = config('DEBUG', default=True, cast=bool)

# Production settings:
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


# Application definition

INSTALLED_APPS = (
    'dal',
    'dal_select2',
    'django_admin_listfilter_dropdown',
    'django_filters',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'mptt',
    'polymorphic',
    'rangefilter',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_docs',
    'reversion',
    'test_without_migrations',
    # alyx-apps
    'actions',
    'data',
    'misc',
    'experiments',
    'subjects',
    'buffalo',
    'crispy_forms',
    'nested_admin',
    'django_cleanup',
    'django_dramatiq',
)

CRISPY_TEMPLATE_PACK = 'bootstrap4'


MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'alyx.base.QueryPrintingMiddleware',
)

ROOT_URLCONF = 'alyx.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)

WSGI_APPLICATION = 'alyx.wsgi.application'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'STRICT_JSON': False,
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    # 'DEFAULT_RENDERER_CLASSES': (
    #     'rest_framework.renderers.JSONRenderer',
    # ),
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'PAGE_SIZE': 250,
}

REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', default='6379')

DRAMATIQ_BROKER = {
    "BROKER": "dramatiq.brokers.redis.RedisBroker",
    "OPTIONS": {
        "host": REDIS_HOST,
        "port": REDIS_PORT,
    },
    "MIDDLEWARE": [
        "dramatiq.middleware.AgeLimit",
        "dramatiq.middleware.TimeLimit",
        "dramatiq.middleware.Callbacks",
        "dramatiq.middleware.Pipelines",
        "dramatiq.middleware.Retries",
        "django_dramatiq.middleware.AdminMiddleware",
        "django_dramatiq.middleware.DbConnectionsMiddleware",
    ]
}

DRAMATIQ_RESULT_BACKEND = {
    "BACKEND": "dramatiq.results.backends.redis.RedisBackend",
    "BACKEND_OPTIONS": {
        "url": f"redis://{REDIS_HOST}:{REDIS_PORT}",
    },
    # "MIDDLEWARE_OPTIONS": {
    #    "result_ttl": 50*24*60*60,
    # },
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/


USE_I18N = False
USE_L10N = False
USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.realpath(os.path.join(BASE_DIR, '../uploaded/'))
MEDIA_URL = '/uploaded/'
UPLOADED_IMAGE_WIDTH = 800

TIME_ZONE = config('TIME_ZONE', default='UTC')

TESTING = config("TESTING", default=False, cast=bool)
SITE_HEADER = config('SITE_HEADER', default='Alyx')
SITE_TITLE = config('SITE_TITLE', default='Alyx')
SITE_URL = config('SITE_URL', default=None)
SITE_INDEX_TITLE = config('SITE_INDEX_TITLE', default="Welcome to Alyx")
ENABLE_HOME_URLS = config("ENABLE_HOME_URLS", default=True, cast=bool)
ADMIN_URL_PATH_IN_ROOT = config("ADMIN_URL_PATH_IN_ROOT", default=False, cast=bool)

DATE_INPUT_FORMATS = ['%m/%d/%Y']