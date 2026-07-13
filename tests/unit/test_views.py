import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from accounts.models import _compute_bidx
from tests.unit.conftest import TEST_BLIND_INDEX_KEY

User = get_user_model()


@pytest.fixture
def client():
    return Client()


def _post_data(**overrides):
    data = {
        'email': 'test@example.com',
        'password': '',
        'password_confirmation': '',
        'current_password': 'correct-password',
        'name': 'Test User',
        'institution': 'Test Uni',
        'country': 'GB',
        'funded': '',
        'mailing_list': '',
        'faculty': '',
        'research_level': 'Staff',
    }
    data.update(overrides)
    return data


# ── GET /settings/ ────────────────────────────────────────────────────────────

class TestProfileEditGet:
    def test_unauthenticated_redirects_to_login(self, client):
        response = client.get(reverse('accounts:profile_edit'))
        assert response.status_code == 302
        assert 'login' in response['Location']

    def test_authenticated_returns_200(self, client, user):
        client.force_login(user)
        response = client.get(reverse('accounts:profile_edit'))
        assert response.status_code == 200

    def test_form_prefilled_with_email(self, client, user):
        client.force_login(user)
        response = client.get(reverse('accounts:profile_edit'))
        assert b'test@example.com' in response.content

    def test_form_prefilled_with_name(self, client, user):
        client.force_login(user)
        response = client.get(reverse('accounts:profile_edit'))
        assert b'Test User' in response.content


# ── POST /settings/ ───────────────────────────────────────────────────────────

class TestProfileEditPost:
    def test_valid_post_redirects(self, client, user):
        client.force_login(user)
        response = client.post(reverse('accounts:profile_edit'), _post_data())
        assert response.status_code == 302

    def test_valid_post_updates_name(self, client, user):
        client.force_login(user)
        client.post(reverse('accounts:profile_edit'), _post_data(name='New Name'))
        user.refresh_from_db()
        assert user.name == 'New Name'

    def test_valid_post_updates_institution(self, client, user):
        client.force_login(user)
        client.post(reverse('accounts:profile_edit'), _post_data(institution='New Uni'))
        user.refresh_from_db()
        assert user.institution == 'New Uni'

    def test_valid_post_updates_email_and_bidx(self, client, user):
        client.force_login(user)
        client.post(reverse('accounts:profile_edit'), _post_data(email='new@example.com'))
        user.refresh_from_db()
        assert user.email == 'new@example.com'
        assert user.email_bidx == _compute_bidx('new@example.com', TEST_BLIND_INDEX_KEY)

    def test_valid_post_with_password_change(self, client, user):
        client.force_login(user)
        client.post(
            reverse('accounts:profile_edit'),
            _post_data(password='NewPass123!', password_confirmation='NewPass123!'),
        )
        user.refresh_from_db()
        assert user.check_password('NewPass123!')

    def test_no_password_in_post_does_not_clear_password(self, client, user):
        client.force_login(user)
        client.post(reverse('accounts:profile_edit'), _post_data(password='', password_confirmation=''))
        user.refresh_from_db()
        assert user.check_password('correct-password')

    def test_success_flash_message_shown(self, client, user):
        client.force_login(user)
        response = client.post(reverse('accounts:profile_edit'), _post_data(), follow=True)
        messages = [str(m) for m in response.context['messages']]
        assert any('updated' in m.lower() for m in messages)

    def test_wrong_current_password_rerenders_form(self, client, user):
        client.force_login(user)
        response = client.post(
            reverse('accounts:profile_edit'),
            _post_data(current_password='wrong'),
        )
        assert response.status_code == 200

    def test_wrong_current_password_does_not_save(self, client, user):
        client.force_login(user)
        client.post(
            reverse('accounts:profile_edit'),
            _post_data(current_password='wrong', name='Hacked Name'),
        )
        user.refresh_from_db()
        assert user.name == 'Test User'

    def test_password_mismatch_rerenders_form(self, client, user):
        client.force_login(user)
        response = client.post(
            reverse('accounts:profile_edit'),
            _post_data(password='NewPass123!', password_confirmation='Different!'),
        )
        assert response.status_code == 200

    def test_password_mismatch_does_not_change_password(self, client, user):
        client.force_login(user)
        client.post(
            reverse('accounts:profile_edit'),
            _post_data(password='NewPass123!', password_confirmation='Different!'),
        )
        user.refresh_from_db()
        assert user.check_password('correct-password')

    def test_unauthenticated_post_redirects(self, client):
        response = client.post(reverse('accounts:profile_edit'), _post_data())
        assert response.status_code == 302
        assert 'login' in response['Location']


# ── POST /settings/cancel/ ────────────────────────────────────────────────────

class TestAccountDeleteView:
    def test_deletes_user(self, client, user):
        pk = user.pk
        client.force_login(user)
        client.post(reverse('accounts:account_delete'))
        assert not User.objects.filter(pk=pk).exists()

    def test_redirects_after_deletion(self, client, user):
        client.force_login(user)
        response = client.post(reverse('accounts:account_delete'))
        assert response.status_code == 302

    def test_logs_user_out_after_deletion(self, client, user):
        client.force_login(user)
        client.post(reverse('accounts:account_delete'))
        response = client.get(reverse('accounts:profile_edit'))
        assert response.status_code == 302
        assert 'login' in response['Location']

    def test_unauthenticated_post_does_not_delete(self, client, user):
        pk = user.pk
        client.post(reverse('accounts:account_delete'))
        assert User.objects.filter(pk=pk).exists()
