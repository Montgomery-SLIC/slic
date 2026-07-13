from .base import *
from dotenv import load_dotenv

load_dotenv(BASE_DIR / '.env')

DEBUG = True

# WhiteNoise serves from STATIC_ROOT (collectstatic output), which goes stale
# during development. Remove it so Django's runserver serves from STATICFILES_DIRS directly
MIDDLEWARE = [m for m in MIDDLEWARE if m != 'whitenoise.middleware.WhiteNoiseMiddleware']
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-not-for-production')
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'slic_django_dev'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}

SILENCED_SYSTEM_CHECKS = ['django_recaptcha.recaptcha_test_key_error']
RECAPTCHA_PUBLIC_KEY = ''
RECAPTCHA_PRIVATE_KEY = ''

BLIND_INDEX_KEY = os.environ.get('BLIND_INDEX_KEY', '')
FIELD_ENCRYPTION_KEY = os.environ.get('FIELD_ENCRYPTION_KEY', '')

MEDIA_ROOT = BASE_DIR / 'media'

X_ACCEL_REDIRECT = False  # Serve media directly in development
