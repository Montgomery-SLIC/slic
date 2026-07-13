import uuid
from django.db import models
from django.db.models import Count
from django.conf import settings
from django.urls import reverse

from responses.models import ParticipantId, Visit


class Experiment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='experiments'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    complete = models.BooleanField(default=False)
    slug = models.SlugField(max_length=36, unique=True, blank=True)
    terms = models.TextField(blank=True, default='')
    results = models.FileField(upload_to='results/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'experiments'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def allowed_task_types(self):
        return ['QuestionTask', 'SampleTask', 'IntermediateScreenTask']

    def total_responses(self):
        return ParticipantId.objects.filter(experiment=self).count()

    def finished_responses(self):
        task_count = self.tasks.count()
        if task_count == 0:
            return 0
        return (
            Visit.objects
            .filter(task__experiment=self, visited=True)
            .values('participant_id')
            .annotate(n=Count('id'))
            .filter(n=task_count)
            .count()
        )

    def last_response_date(self):
        last = ParticipantId.objects.filter(experiment=self).order_by('-created_at').first()
        return last.created_at if last else None

    def completion_errors(self):
        warnings, errors = [], []
        tasks = self.tasks.order_by('sort')
        if not tasks.exists():
            errors.append(f"'{self.name}' does not contain any tasks.")
        for task in tasks:
            specific = task.get_specific()
            if specific is not None and hasattr(specific, 'completion_errors'):
                te = specific.completion_errors()
                warnings.extend(te['warnings'])
                errors.extend(te['errors'])
        return {'warnings': warnings, 'errors': errors}

    def get_absolute_url(self):
        return reverse('experiments:show', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name
