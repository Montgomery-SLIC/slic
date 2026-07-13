import pytest
from django.contrib.auth import get_user_model

from accounts.models import _compute_bidx
from tests.unit.conftest import TEST_BLIND_INDEX_KEY

User = get_user_model()


class TestComputeBidx:
    def test_produces_64_char_hex_string(self):
        result = _compute_bidx('test@example.com', TEST_BLIND_INDEX_KEY)
        assert len(result) == 64
        assert all(c in '0123456789abcdef' for c in result)

    def test_same_input_same_output(self):
        a = _compute_bidx('test@example.com', TEST_BLIND_INDEX_KEY)
        b = _compute_bidx('test@example.com', TEST_BLIND_INDEX_KEY)
        assert a == b

    def test_different_emails_different_bidx(self):
        a = _compute_bidx('alice@example.com', TEST_BLIND_INDEX_KEY)
        b = _compute_bidx('bob@example.com', TEST_BLIND_INDEX_KEY)
        assert a != b

    def test_case_insensitive(self):
        lower = _compute_bidx('test@example.com', TEST_BLIND_INDEX_KEY)
        upper = _compute_bidx('TEST@EXAMPLE.COM', TEST_BLIND_INDEX_KEY)
        assert lower == upper

    def test_strips_whitespace(self):
        plain = _compute_bidx('test@example.com', TEST_BLIND_INDEX_KEY)
        padded = _compute_bidx('  test@example.com  ', TEST_BLIND_INDEX_KEY)
        assert plain == padded


class TestUserEmailProperty:
    @pytest.mark.django_db
    def test_setter_stores_plaintext_in_ciphertext_field(self):
        u = User()
        u.email = 'stored@example.com'
        assert u.email_ciphertext == 'stored@example.com'

    @pytest.mark.django_db
    def test_getter_returns_ciphertext_value(self):
        u = User()
        u.email = 'stored@example.com'
        assert u.email == 'stored@example.com'

    @pytest.mark.django_db
    def test_setter_computes_bidx(self):
        u = User()
        u.email = 'stored@example.com'
        expected = _compute_bidx('stored@example.com', TEST_BLIND_INDEX_KEY)
        assert u.email_bidx == expected

    @pytest.mark.django_db
    def test_empty_blind_index_key_gives_empty_bidx(self, settings):
        settings.BLIND_INDEX_KEY = ''
        u = User()
        u.email = 'stored@example.com'
        assert u.email_bidx == ''


class TestUserManagerGetByNaturalKey:
    @pytest.mark.django_db
    def test_finds_user_by_email(self, user):
        found = User.objects.get_by_natural_key('test@example.com')
        assert found.pk == user.pk

    @pytest.mark.django_db
    def test_lookup_is_case_insensitive(self, user):
        found = User.objects.get_by_natural_key('TEST@EXAMPLE.COM')
        assert found.pk == user.pk

    @pytest.mark.django_db
    def test_raises_does_not_exist_for_missing_email(self, db):
        with pytest.raises(User.DoesNotExist):
            User.objects.get_by_natural_key('nobody@example.com')


class TestUserProfileFields:
    @pytest.mark.django_db
    def test_name_stored_and_retrieved(self, user):
        assert user.name == 'Test User'

    @pytest.mark.django_db
    def test_institution_stored_and_retrieved(self, user):
        assert user.institution == 'Test Uni'

    @pytest.mark.django_db
    def test_country_stored_and_retrieved(self, user):
        assert user.country == 'GB'

    @pytest.mark.django_db
    def test_research_level_stored_and_retrieved(self, user):
        assert user.research_level == 'Staff'

    @pytest.mark.django_db
    def test_str_returns_email(self, user):
        assert str(user) == 'test@example.com'
