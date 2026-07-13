import secrets
from django.conf import settings
from django.db import models
from encrypted_model_fields.fields import EncryptedTextField

from accounts.models import _compute_bidx


class Visit(models.Model):
    participant_id = models.IntegerField()
    task = models.ForeignKey('tasks.Task', on_delete=models.CASCADE, related_name='visits')
    visited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'visits'
        unique_together = [('participant_id', 'task')]

    def __str__(self):
        return f'Visit pid={self.participant_id} task={self.task_id}'


class ParticipantId(models.Model):
    experiment = models.ForeignKey(
        'experiments.Experiment', on_delete=models.CASCADE, related_name='participant_ids'
    )
    participant_id = models.IntegerField()
    email_ciphertext = EncryptedTextField(null=True, blank=True)
    email_bidx = models.CharField(max_length=64, blank=True, default='')
    slug = models.CharField(max_length=32, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'participant_ids'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = secrets.token_urlsafe(16)
        super().save(*args, **kwargs)

    @property
    def email(self):
        return self.email_ciphertext or ''

    @email.setter
    def email(self, value):
        self.email_ciphertext = value
        key_hex = settings.BLIND_INDEX_KEY
        self.email_bidx = _compute_bidx(value, key_hex) if value and key_hex else ''


class Response(models.Model):
    participant_id = models.IntegerField()
    question = models.ForeignKey('tasks.Question', on_delete=models.CASCADE, related_name='responses')
    answer_ciphertext = EncryptedTextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'responses'

    @property
    def answer(self):
        return self.answer_ciphertext or ''

    @answer.setter
    def answer(self, value):
        self.answer_ciphertext = value


class ClickResponse(models.Model):
    participant_id = models.IntegerField()
    click_task = models.ForeignKey('tasks.ClickTask', on_delete=models.CASCADE, related_name='click_responses')
    time = models.FloatField(null=True, blank=True)
    answer_ciphertext = EncryptedTextField(null=True, blank=True)
    no_clicks_explanation = models.BooleanField(default=False)
    from_checkbox = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'click_responses'

    @property
    def answer(self):
        return self.answer_ciphertext or ''

    @answer.setter
    def answer(self, value):
        self.answer_ciphertext = value
