from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from responses.models import Visit


class Task(models.Model):
    """Base task. Owned by exactly one of: Experiment or SampleTask."""
    name = models.CharField(max_length=255)
    experiment = models.ForeignKey(
        'experiments.Experiment', null=True, blank=True,
        on_delete=models.CASCADE, related_name='tasks',
    )
    sample_task = models.ForeignKey(
        'tasks.SampleTask', null=True, blank=True,
        on_delete=models.CASCADE, related_name='subtasks',
    )
    sort = models.IntegerField(null=True, blank=True)
    random = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tasks'
        ordering = ['sort']
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(experiment__isnull=False, sample_task__isnull=True) |
                    models.Q(experiment__isnull=True, sample_task__isnull=False)
                ),
                name='task_has_exactly_one_owner',
            )
        ]

    def get_owner(self):
        return self.experiment or self.sample_task

    def get_experiment_pk(self):
        if self.experiment_id:
            return self.experiment_id
        return self.sample_task.experiment_id

    def get_specific(self):
        for attr in ('questiontask', 'sampletask', 'listeningtask', 'clicktask', 'intermediatescreentask'):
            try:
                return getattr(self, attr)
            except Exception:
                pass
        return None

    def mark_visited(self, participant_id):
        Visit.objects.filter(task=self, participant_id=participant_id).update(visited=True)

    def __str__(self):
        return self.name


class QuestionTask(Task):
    class Meta:
        db_table = 'question_tasks'

    def type_name(self):
        return 'Question page'

    def allowed_subtask_types(self):
        return []

    def completion_errors(self):
        warnings, errors = [], []
        for q in self.questions.all():
            qe = q.completion_errors()
            warnings.extend(qe['warnings'])
            errors.extend(qe['errors'])
        if not self.questions.exists():
            errors.append(f"Question page '{self.name}' does not contain any questions.")
        return {'warnings': warnings, 'errors': errors}


class SampleTask(Task):
    calibration = models.BooleanField(default=False)
    audio = models.FileField(upload_to='audio/', null=True, blank=True)
    transcript = models.FileField(upload_to='transcripts/', null=True, blank=True)

    class Meta:
        db_table = 'sample_tasks'

    def type_name(self):
        return 'Audio sample'

    def allowed_subtask_types(self):
        return ['QuestionTask', 'ListeningTask', 'ClickTask', 'IntermediateScreenTask']

    def completion_errors(self):
        warnings, errors = [], []
        has_click_task = False
        for subtask in self.subtasks.all():
            specific = subtask.get_specific()
            if specific is not None and hasattr(specific, 'completion_errors'):
                se = specific.completion_errors()
                warnings.extend(se['warnings'])
                errors.extend(se['errors'])
            if isinstance(specific, ClickTask):
                has_click_task = True
        if not self.audio:
            errors.append(f"Audio sample '{self.name}' has no audio file attached.")
        if has_click_task and not self.transcript and not self.calibration:
            errors.append(
                f"Audio sample '{self.name}' has reaction tasks but has no transcript file attached."
            )
        if self.calibration and not has_click_task:
            warnings.append(
                f"Audio sample '{self.name}' is marked as a calibration sample but has no click tasks."
            )
        return {'warnings': warnings, 'errors': errors}


class ListeningTask(Task):
    listens = models.IntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        db_table = 'listening_tasks'

    def type_name(self):
        return 'Audio hearing'

    def completion_errors(self):
        return {'warnings': [], 'errors': []}


class ClickTask(Task):
    prompt = models.TextField(null=True, blank=True)
    explanation_prompt = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'click_tasks'

    def type_name(self):
        return 'Reaction task'

    def completion_errors(self):
        return {'warnings': [], 'errors': []}


class IntermediateScreenTask(Task):
    message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'intermediate_screen_tasks'

    def type_name(self):
        return 'Intermediate screen'

    def completion_errors(self):
        return {'warnings': [], 'errors': []}


QUESTION_TYPE_TEXT = 'text'
QUESTION_TYPE_CHECKBOX = 'checkbox'
QUESTION_TYPE_RADIO = 'radio'
QUESTION_TYPE_DROPDOWN = 'dropdown'
QUESTION_TYPE_RATING = 'rating'

QUESTION_TYPE_CHOICES = [
    (QUESTION_TYPE_TEXT, 'Text question'),
    (QUESTION_TYPE_CHECKBOX, 'Checkboxes'),
    (QUESTION_TYPE_RADIO, 'Radio buttons'),
    (QUESTION_TYPE_DROPDOWN, 'Dropdown box'),
    (QUESTION_TYPE_RATING, 'Rating scale'),
]

# Default prompt set at creation time; warning fires if prompt is still this value.
QUESTION_DEFAULT_PROMPTS = {
    QUESTION_TYPE_TEXT: 'New text question',
    QUESTION_TYPE_CHECKBOX: 'New checkboxes',
    QUESTION_TYPE_RADIO: 'New radio buttons',
    QUESTION_TYPE_DROPDOWN: 'New dropdown box',
    QUESTION_TYPE_RATING: 'New rating scale',
}

# For use by the data migration (Step 3)
RAILS_STI_TYPE_MAP = {
    'Question::Text': QUESTION_TYPE_TEXT,
    'Question::Checkbox': QUESTION_TYPE_CHECKBOX,
    'Question::Radio': QUESTION_TYPE_RADIO,
    'Question::Dropdown': QUESTION_TYPE_DROPDOWN,
    'Question::Rating': QUESTION_TYPE_RATING,
}


class Question(models.Model):
    question_task = models.ForeignKey(
        QuestionTask, on_delete=models.CASCADE, related_name='questions'
    )
    question_type = models.CharField(
        max_length=20, choices=QUESTION_TYPE_CHOICES, default=QUESTION_TYPE_TEXT
    )
    prompt = models.TextField(blank=True, default='')
    sort = models.IntegerField(null=True, blank=True)
    required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'questions'
        ordering = ['sort']

    def has_options(self):
        return self.question_type in (
            QUESTION_TYPE_CHECKBOX, QUESTION_TYPE_RADIO, QUESTION_TYPE_DROPDOWN
        )

    def completion_errors(self):
        warnings, errors = [], []
        qt_name = self.question_task.name
        display = dict(QUESTION_TYPE_CHOICES).get(self.question_type, self.question_type)
        default_prompt = QUESTION_DEFAULT_PROMPTS.get(self.question_type, '')
        if self.prompt == default_prompt:
            warnings.append(f"{display} in '{qt_name}' still has default prompt.")
        if self.has_options() and not self.options.exists():
            errors.append(f"{display} in '{qt_name}' has no options.")
        if self.question_type == QUESTION_TYPE_RATING:
            if not Scale.objects.filter(question=self).exists():
                errors.append(f"Rating scale in '{qt_name}' has no scale configured.")
        return {'warnings': warnings, 'errors': errors}

    def __str__(self):
        return self.prompt or f'Question {self.pk}'


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    contents = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'options'

    def __str__(self):
        return self.contents


class Scale(models.Model):
    question = models.OneToOneField(
        Question, on_delete=models.CASCADE, related_name='scale',
        limit_choices_to={'question_type': QUESTION_TYPE_RATING},
    )
    bins = models.IntegerField(validators=[MinValueValidator(2), MaxValueValidator(20)])
    low = models.CharField(max_length=255, blank=True, default='')
    high = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scales'

    @property
    def bins_range(self):
        return range(1, self.bins + 1)

    def __str__(self):
        return f'Scale ({self.low} – {self.high}, {self.bins} bins)'
