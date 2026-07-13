from django import forms
from django.core.exceptions import ValidationError
from django_countries.fields import CountryField
from .models import ResearcherInvitation

RESEARCH_LEVEL_CHOICES = [
    ('', '-- Select --'),
    ('Undergraduate', 'Undergraduate'),
    ('Postgraduate', 'Postgraduate'),
    ('Staff', 'Staff'),
]


class ProfileEditForm(forms.Form):
    email = forms.EmailField(label='Email', required=True)
    password = forms.CharField(
        label='Password',
        required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text="Leave it blank if you don't want to change it.",
    )
    password_confirmation = forms.CharField(
        label='Password confirmation',
        required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    current_password = forms.CharField(
        label='Current password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
        help_text='We need your current password to confirm your changes.',
    )
    name = forms.CharField(max_length=255, label='Name', required=True)
    institution = forms.CharField(max_length=255, label='Institution', required=False)
    country = CountryField().formfield(label='Country', required=True)
    funded = forms.BooleanField(required=False, label='Funded')
    mailing_list = forms.BooleanField(required=False, label='Mailing list')
    faculty = forms.CharField(max_length=255, label='Faculty', required=False)
    research_level = forms.ChoiceField(
        choices=RESEARCH_LEVEL_CHOICES,
        label='Research level',
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
            raise forms.ValidationError('Your current password is incorrect.')
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirmation = cleaned_data.get('password_confirmation')
        if password and password != confirmation:
            self.add_error('password_confirmation', 'Passwords do not match.')
        return cleaned_data


class ResearcherSignupForm(forms.Form):
    registration_code = forms.CharField(
        max_length=255,
        label='Registration code',
        help_text='You need an invitation code to register.',
    )
    name = forms.CharField(max_length=255, label='Full name')
    institution = forms.CharField(max_length=255, label='Institution')
    country = CountryField().formfield(label='Country')
    faculty = forms.CharField(max_length=255, label='Faculty / Department', required=False)
    research_level = forms.ChoiceField(choices=RESEARCH_LEVEL_CHOICES, label='Research level')
    funded = forms.BooleanField(
        required=False,
        label='My research is externally funded',
    )
    mailing_list = forms.BooleanField(
        required=False,
        label='I would like to join the SLIC mailing list',
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
