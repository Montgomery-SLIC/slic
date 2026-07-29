from django.conf import settings
from django.contrib.auth import get_user_model
from allauth.account.forms import ResetPasswordForm
from allauth.account import app_settings as allauth_app_settings
from allauth.account.adapter import get_adapter as allauth_get_adapter

from .models import _compute_bidx


class ResearcherResetPasswordForm(ResetPasswordForm):
    """Override allauth's reset form to find users via HMAC blind index.

    The standard allauth lookup queries the email field directly, which does
    not work because our email is Fernet-encrypted. We use the HMAC blind
    index instead to locate the matching user.
    """

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        email = allauth_get_adapter().clean_email(email)
        bidx = _compute_bidx(email, settings.BLIND_INDEX_KEY)
        User = get_user_model()
        self.users = list(User.objects.filter(email_bidx=bidx, is_active=True))
        if not self.users and not allauth_app_settings.PREVENT_ENUMERATION:
            raise allauth_get_adapter().validation_error('unknown_email')
        return self.cleaned_data['email']
