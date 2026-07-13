import pytest
from django.contrib.auth import get_user_model

from accounts.backends import HMACEmailBackend

User = get_user_model()


@pytest.fixture
def backend():
    return HMACEmailBackend()


class TestHMACEmailBackend:
    def test_correct_credentials_returns_user(self, backend, user):
        result = backend._authenticate_by_email(
            email='test@example.com', password='correct-password'
        )
        assert result is not None
        assert result.pk == user.pk

    def test_wrong_password_returns_none(self, backend, user):
        result = backend._authenticate_by_email(
            email='test@example.com', password='wrong-password'
        )
        assert result is None

    def test_nonexistent_email_returns_none(self, backend, db):
        result = backend._authenticate_by_email(
            email='nobody@example.com', password='any-password'
        )
        assert result is None

    def test_empty_email_returns_none(self, backend):
        result = backend._authenticate_by_email(email='', password='any-password')
        assert result is None

    def test_empty_password_returns_none(self, backend, user):
        result = backend._authenticate_by_email(
            email='test@example.com', password=''
        )
        assert result is None

    def test_inactive_user_returns_none(self, backend, user):
        user.is_active = False
        user.save(update_fields=['is_active'])
        result = backend._authenticate_by_email(
            email='test@example.com', password='correct-password'
        )
        assert result is None
