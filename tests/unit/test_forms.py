import pytest
from accounts.forms import ProfileEditForm


def _base_data(**overrides):
    data = {
        'email': 'test@example.com',
        'password': '',
        'password_confirmation': '',
        'current_password': 'correct-password',
        'name': 'Test User',
        'institution': 'Test Uni',
        'country': 'GB',
        'funded': False,
        'mailing_list': False,
        'faculty': '',
        'research_level': 'Staff',
    }
    data.update(overrides)
    return data


class TestProfileEditFormValid:
    def test_valid_no_password_change(self, user):
        form = ProfileEditForm(data=_base_data(), user=user)
        assert form.is_valid(), form.errors

    def test_valid_with_password_change(self, user):
        form = ProfileEditForm(
            data=_base_data(password='NewPass123!', password_confirmation='NewPass123!'),
            user=user,
        )
        assert form.is_valid(), form.errors

    def test_institution_optional(self, user):
        form = ProfileEditForm(data=_base_data(institution=''), user=user)
        assert form.is_valid(), form.errors

    def test_faculty_optional(self, user):
        form = ProfileEditForm(data=_base_data(faculty=''), user=user)
        assert form.is_valid(), form.errors

    def test_funded_defaults_false_when_omitted(self, user):
        data = _base_data()
        data.pop('funded')
        form = ProfileEditForm(data=data, user=user)
        assert form.is_valid(), form.errors
        assert form.cleaned_data['funded'] is False

    def test_mailing_list_defaults_false_when_omitted(self, user):
        data = _base_data()
        data.pop('mailing_list')
        form = ProfileEditForm(data=data, user=user)
        assert form.is_valid(), form.errors
        assert form.cleaned_data['mailing_list'] is False

    def test_all_research_level_choices_accepted(self, user):
        for level in ('Undergraduate', 'Postgraduate', 'Staff'):
            form = ProfileEditForm(data=_base_data(research_level=level), user=user)
            assert form.is_valid(), f"Expected {level!r} to be valid; errors: {form.errors}"


class TestProfileEditFormCurrentPassword:
    def test_wrong_current_password_rejected(self, user):
        form = ProfileEditForm(data=_base_data(current_password='wrong'), user=user)
        assert not form.is_valid()
        assert 'current_password' in form.errors

    def test_empty_current_password_rejected(self, user):
        form = ProfileEditForm(data=_base_data(current_password=''), user=user)
        assert not form.is_valid()
        assert 'current_password' in form.errors


class TestProfileEditFormPasswordChange:
    def test_mismatched_passwords_rejected(self, user):
        form = ProfileEditForm(
            data=_base_data(password='NewPass123!', password_confirmation='Different!'),
            user=user,
        )
        assert not form.is_valid()
        assert 'password_confirmation' in form.errors

    def test_new_password_without_confirmation_rejected(self, user):
        form = ProfileEditForm(
            data=_base_data(password='NewPass123!', password_confirmation=''),
            user=user,
        )
        assert not form.is_valid()
        assert 'password_confirmation' in form.errors

    def test_blank_password_fields_mean_no_change(self, user):
        form = ProfileEditForm(data=_base_data(password='', password_confirmation=''), user=user)
        assert form.is_valid(), form.errors
        assert form.cleaned_data['password'] == ''


class TestProfileEditFormRequiredFields:
    def test_email_required(self, user):
        form = ProfileEditForm(data=_base_data(email=''), user=user)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_invalid_email_format_rejected(self, user):
        form = ProfileEditForm(data=_base_data(email='not-an-email'), user=user)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_name_required(self, user):
        form = ProfileEditForm(data=_base_data(name=''), user=user)
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_country_required(self, user):
        form = ProfileEditForm(data=_base_data(country=''), user=user)
        assert not form.is_valid()
        assert 'country' in form.errors

    def test_research_level_required(self, user):
        form = ProfileEditForm(data=_base_data(research_level=''), user=user)
        assert not form.is_valid()
        assert 'research_level' in form.errors

    def test_invalid_research_level_rejected(self, user):
        form = ProfileEditForm(data=_base_data(research_level='Professor'), user=user)
        assert not form.is_valid()
        assert 'research_level' in form.errors
