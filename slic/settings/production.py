from dotenv import load_dotenv

load_dotenv()

from .base import *

DEBUG = False
SECRET_KEY = os.environ['SECRET_KEY']
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'slic_django'),
        'USER': os.environ.get('DB_USER', 'slic'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 60,
    }
}

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True

STATIC_ROOT = os.environ.get('STATIC_ROOT', '/srv/slic/production/slic/staticfiles')
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', '/srv/slic/production/media')

RECAPTCHA_PUBLIC_KEY = os.environ['RECAPTCHA_PUBLIC_KEY']
RECAPTCHA_PRIVATE_KEY = os.environ['RECAPTCHA_PRIVATE_KEY']
BLIND_INDEX_KEY = os.environ['BLIND_INDEX_KEY']
FIELD_ENCRYPTION_KEY = os.environ['FIELD_ENCRYPTION_KEY']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/slic/django.log',
            'formatter': 'verbose',
        },
    },
    'root': {'handlers': ['file'], 'level': 'WARNING'},
    'loggers': {
        'django': {'handlers': ['file'], 'level': 'WARNING', 'propagate': False},
    },
}

_admin_email = os.environ.get('ADMIN_EMAIL', '')
ADMINS = [(os.environ.get('ADMIN_NAME', 'Admin'), _admin_email)] if _admin_email else []
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', 'root@slic.shef.ac.uk')
BUG_REPORT_EMAIL = os.environ['BUG_REPORT_EMAIL']
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 25))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'false').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

X_ACCEL_REDIRECT = True
