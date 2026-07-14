from django.conf import settings
from slic import __version__


def recaptcha_key(request):
    return {'RECAPTCHA_PUBLIC_KEY': getattr(settings, 'RECAPTCHA_PUBLIC_KEY', '')}


def slic_version(request):
    return {'SLIC_VERSION': __version__}
