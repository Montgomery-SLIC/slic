import pytest
from django.contrib.auth import get_user_model

# A fixed 32-byte (64 hex char) key used across all unit tests.
TEST_BLIND_INDEX_KEY = 'ab' * 32

User = get_user_model()


@pytest.fixture(autouse=True)
def patch_blind_index_key(settings):
    """Ensure every unit test has a consistent BLIND_INDEX_KEY.

    Without this, the email_bidx unique constraint causes the second user
    created across tests to collide (all bidx values would be '').
    """
    settings.BLIND_INDEX_KEY = TEST_BLIND_INDEX_KEY


@pytest.fixture
def user(db):
    u = User()
    u.email = 'test@example.com'
    u.name = 'Test User'
    u.institution = 'Test Uni'
    u.country = 'GB'
    u.research_level = 'Staff'
    u.funded = False
    u.mailing_list = False
    u.set_password('correct-password')
    u.save()
    return u
