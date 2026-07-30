from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from .models import ResearcherInvitation

RESEARCH_LEVEL_CHOICES = [
    ('', _('-- Select --')),
    ('Undergraduate', _('Undergraduate')),
    ('Postgraduate', _('Postgraduate')),
    ('Staff', _('Staff')),
]


class ProfileEditForm(forms.Form):
    email = forms.EmailField(label=_('Email'), required=True)
    password = forms.CharField(
        label=_('Password'),
        required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text=_("Leave it blank if you don't want to change it."),
    )
    password_confirmation = forms.CharField(
        label=_('Password confirmation'),
        required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    current_password = forms.CharField(
        label=_('Current password'),
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
        help_text=_('We need your current password to confirm your changes.'),
    )
    name = forms.CharField(max_length=255, label=_('Name'), required=True)
    institution = forms.CharField(max_length=255, label=_('Institution'), required=False)
    country = CountryField().formfield(label=_('Country'), required=True)
    funded = forms.BooleanField(required=False, label=_('Funded'))
    mailing_list = forms.BooleanField(required=False, label=_('Mailing list'))
    faculty = forms.CharField(max_length=255, label=_('Faculty'), required=False)
    research_level = forms.ChoiceField(
        choices=RESEARCH_LEVEL_CHOICES,
        label=_('Research level'),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['country'].widget.attrs.update({'class': 'form-control'})

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if self.user and not self.user.check_password(current_password):
            raise forms.ValidationError(_('Your current password is incorrect.'))
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirmation = cleaned_data.get('password_confirmation')
        if password and password != confirmation:
            self.add_error('password_confirmation', _('Passwords do not match.'))
        return cleaned_data


class ResearcherSignupForm(forms.Form):
    registration_code = forms.CharField(
        max_length=255,
        label=_('Registration code'),
        help_text=_('You need an invitation code to register.'),
    )
    name = forms.CharField(max_length=255, label=_('Full name'))
    institution = forms.CharField(max_length=255, label=_('Institution'))
    country = CountryField().formfield(label=_('Country'))
    faculty = forms.CharField(max_length=255, label=_('Faculty / Department'), required=False)
    research_level = forms.ChoiceField(choices=RESEARCH_LEVEL_CHOICES, label=_('Research level'))
    funded = forms.BooleanField(
        required=False,
        label=_('My research is externally funded'),
    )
    mailing_list = forms.BooleanField(
        required=False,
        label=_('I would like to join the SLIC mailing list'),
    )

    def clean_registration_code(self):
        code = self.cleaned_data.get('registration_code', '').strip()
        try:
            invitation = ResearcherInvitation.objects.get(registration_code=code, used=False)
            self.invitation = invitation
        except ResearcherInvitation.DoesNotExist:
            raise ValidationError('Invalid or already-used registration code.')
        return code

    def signup(self, request, user):
        pass
