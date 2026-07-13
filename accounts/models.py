import hmac
import hashlib
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings

from encrypted_model_fields.fields import EncryptedTextField


def _compute_bidx(value: str, key_hex: str) -> str:
    key = bytes.fromhex(key_hex)
    return hmac.new(key, value.lower().strip().encode('utf-8'), hashlib.sha256).hexdigest()


class UserManager(BaseUserManager):
    def get_by_natural_key(self, email):
        key_hex = settings.BLIND_INDEX_KEY
        bidx = _compute_bidx(email, key_hex)
        return self.get(email_bidx=bidx)

    def create_user(self, email_bidx, password=None, **extra_fields):
        if not email_bidx:
            raise ValueError('Email is required')
        user = self.model(**extra_fields)
        user.email = email_bidx
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email_bidx, password=None, **extra_fields):
        extra_fields.setdefault('admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email_bidx, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email_ciphertext = EncryptedTextField(null=True, blank=True)
    email_bidx = models.CharField(max_length=64, unique=True, db_index=True)
    name_ciphertext = EncryptedTextField(null=True, blank=True)
    institution_ciphertext = EncryptedTextField(null=True, blank=True)
    country_ciphertext = EncryptedTextField(null=True, blank=True)
    faculty_ciphertext = EncryptedTextField(null=True, blank=True)
    research_level_ciphertext = EncryptedTextField(null=True, blank=True)

    # Profile flags
    funded = models.BooleanField(null=True, blank=True)
    mailing_list = models.BooleanField(null=True, blank=True)

    # Auth / account state
    admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    failed_attempts = models.IntegerField(default=0)
    locked_at = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Devise compatibility columns (kept for migration parity - not used by Django auth)
    sign_in_count = models.IntegerField(default=0)
    current_sign_in_at = models.DateTimeField(null=True, blank=True)
    last_sign_in_at = models.DateTimeField(null=True, blank=True)
    current_sign_in_ip = models.GenericIPAddressField(null=True, blank=True)
    last_sign_in_ip = models.GenericIPAddressField(null=True, blank=True)
    reset_password_token = models.CharField(max_length=255, null=True, blank=True, unique=True)
    reset_password_sent_at = models.DateTimeField(null=True, blank=True)
    remember_created_at = models.DateTimeField(null=True, blank=True)
    unlock_token = models.CharField(max_length=255, null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email_bidx'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email or f'User {self.pk}'

    @property
    def email(self):
        return self.email_ciphertext

    @email.setter
    def email(self, value):
        self.email_ciphertext = value
        if value and settings.BLIND_INDEX_KEY:
            self.email_bidx = _compute_bidx(value, settings.BLIND_INDEX_KEY)
        else:
            self.email_bidx = ''

    @property
    def name(self):
        return self.name_ciphertext

    @name.setter
    def name(self, value):
        self.name_ciphertext = value

    @property
    def institution(self):
        return self.institution_ciphertext

    @institution.setter
    def institution(self, value):
        self.institution_ciphertext = value

    @property
    def country(self):
        return self.country_ciphertext

    @country.setter
    def country(self, value):
        self.country_ciphertext = value

    @property
    def faculty(self):
        return self.faculty_ciphertext

    @faculty.setter
    def faculty(self, value):
        self.faculty_ciphertext = value

    @property
    def research_level(self):
        return self.research_level_ciphertext

    @research_level.setter
    def research_level(self, value):
        self.research_level_ciphertext = value


class ResearcherInvitation(models.Model):
    registration_code = models.CharField(max_length=255, unique=True)
    used = models.BooleanField(default=False)
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='invitations',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'researcher_invitations'

    def __str__(self):
        status = 'used' if self.used else 'available'
        return f'{self.registration_code} ({status})'
