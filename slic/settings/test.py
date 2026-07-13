import os
from pathlib import Path
from dotenv import load_dotenv
from .base import *

# Load .env so DB_USER / DB_PASSWORD etc. are available (same file as development.py)
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = 'test-secret-key-do-not-use-in-production'
DEBUG = True
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'slic_django_test'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Valid 32-byte Fernet key (all-zero bytes, test use only - never use in production)
FIELD_ENCRYPTION_KEY = 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='
# 64 hex chars = 32 zero bytes - test HMAC key for blind index
BLIND_INDEX_KEY = '0' * 64

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

SILENCED_SYSTEM_CHECKS = ['django_recaptcha.recaptcha_test_key_error']
RECAPTCHA_PUBLIC_KEY = ''
RECAPTCHA_PRIVATE_KEY = ''  # Empty → ExperimentStartView skips reCAPTCHA check

X_ACCEL_REDIRECT = False

# Avoid needing collectstatic in tests
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}
