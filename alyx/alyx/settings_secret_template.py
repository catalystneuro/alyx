# You should edit this file to match your settings and copy it to
# "settings_secret.py".

from decouple import config

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '%SECRET_KEY%'

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

POSTGRES_HOST = config('POSTGRES_HOST', default='%DBHOST%')
POSTGRES_PORT = config('POSTGRES_PORT', default='5432')
POSTGRES_DB = config('POSTGRES_DB', default='%DBNAME%')
POSTGRES_USER = config('POSTGRES_USER', default='%DBUSER%')
POSTGRES_PASSWORD = config('POSTGRES_PASSWORD', default='%DBPASSWORD%')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': POSTGRES_DB,
        'USER': POSTGRES_USER,
        'PASSWORD': POSTGRES_PASSWORD,
        'HOST': POSTGRES_HOST,
        'PORT': POSTGRES_PORT,
    }
}

EMAIL_HOST = 'mail.superserver.net'
EMAIL_HOST_USER = 'alyx@awesomedomain.org'
EMAIL_HOST_PASSWORD = 'UnbreakablePassword'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
