from django.contrib.auth import get_user_model
from allauth.account.auth_backends import AuthenticationBackend as AllauthBackend


class HMACEmailBackend(AllauthBackend):
    """Auth backend that looks up users via get_by_natural_key (HMAC blind index)

    Replaces allauth's default filter_users_by_email approach, which can't
    work when the email field stores an HMAC rather than the plain address
    """

    def _authenticate_by_email(self, **credentials):
        email = credentials.get('email', '')
        password = credentials.get('password', '')
        if not email or not password:
            return None
        User = get_user_model()
        try:
            user = User.objects.get_by_natural_key(email)
        except User.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
