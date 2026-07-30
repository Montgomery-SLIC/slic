"""
Navigation helpers for the participant and preview flows.

next_task        - Visit-based navigation for real participant sessions.
preview_next_url - Sort-order navigation for researcher preview (no DB reads/writes).
build_task_context / task_template_name - shared rendering helpers used by both flows.
"""
import random as rng
from django.urls import reverse

from tasks.models import Task, SampleTask, QuestionTask, ListeningTask, ClickTask, IntermediateScreenTask
from experiments.models import Experiment
from .models import Visit


# ── Shared rendering helpers ─────────────────────────────────────────────────

def build_task_context(exp, task, specific, sample, next_url, audio_url='', **extra):
    """Build the template context dict for rendering a task page."""
    transcript_content = ''
    if sample and sample.transcript:
        try:
            transcript_content = sample.transcript.read().decode('utf-8')
            sample.transcript.seek(0)
        except Exception:
            transcript_content = ''

    questions = list(specific.questions.order_by('sort')) if isinstance(specific, QuestionTask) else []

    ctx = {
        'experiment': exp,
        'task': task,
        'specific': specific,
        'sample': sample,
        'sample_task': sample,
        'transcript_content': transcript_content,
        'transcript_xml': transcript_content,
        'next_url': next_url,
        'audio_url': audio_url,
        'questions': questions,
        'is_calibration': sample.calibration if sample else False,
    }
    ctx.update(extra)
    return ctx


def task_template_name(specific):
    """Return the template path for a given task type."""
    template_map = {
        'QuestionTask': 'responses/tasks/question_task.html',
        'SampleTask': 'responses/tasks/sample_task.html',
        'ListeningTask': 'responses/tasks/listening_task.html',
        'ClickTask': 'responses/tasks/click_task.html',
        'IntermediateScreenTask': 'responses/tasks/intermediate_screen_task.html',
    }
    return template_map.get(type(specific).__name__, 'responses/tasks/question_task.html')


# ── Visit-based navigation (real participant flow) ───────────────────────────

def _task_url(slug, participant_id, task):
    """Build participant-facing URL for a task."""
    specific = task.get_specific()
    if isinstance(specific, SampleTask):
        return reverse('responses:sample_intro', kwargs={
            'slug': slug, 'participant_id': participant_id, 'sample_id': task.pk,
        })
    type_map = {
        QuestionTask: 'questiontask',
        ListeningTask: 'listeningtask',
        ClickTask: 'clicktask',
        IntermediateScreenTask: 'intermediatescreentask',
    }
    task_type = type_map.get(type(specific), 'task')
    return reverse('responses:task_view', kwargs={
        'slug': slug,
        'participant_id': participant_id,
        'task_type': task_type,
        'task_id': task.pk,
    })


def next_task(taskable, participant_id, slug):
    """
    Return URL of the next task for this participant, or the finish URL.

    taskable: Experiment or SampleTask instance
    """
    if isinstance(taskable, Experiment):
        tasks = list(taskable.tasks.order_by('sort'))
    else:
        tasks = list(taskable.subtasks.order_by('sort'))

    visited_ids = set(
        Visit.objects
        .filter(participant_id=participant_id, task__in=tasks, visited=True)
        .values_list('task_id', flat=True)
    )

    unvisited = [t for t in tasks if t.pk not in visited_ids]

    if not unvisited:
        if isinstance(taskable, SampleTask):
            # Mark the sample task itself as visited so the experiment level won't return it again
            Visit.objects.filter(participant_id=participant_id, task_id=taskable.pk).update(visited=True)
            parent_exp = taskable.experiment
            return next_task(parent_exp, participant_id, slug)
        return reverse('responses:finish', kwargs={'slug': slug, 'participant_id': participant_id})

    # Handle random flag
    if unvisited[0].random:
        random_group = [t for t in unvisited if t.random]
        chosen = rng.choice(random_group)
    else:
        chosen = unvisited[0]

    return _task_url(slug, participant_id, chosen)


# ── Preview navigation (researcher preview - no DB reads/writes) ─────────────

def _preview_url_for_task(exp, task):
    """Build the preview URL for a task."""
    specific = task.get_specific()
    if isinstance(specific, SampleTask):
        return reverse('experiments:preview_sample', kwargs={
            'pk': exp.pk, 'sample_id': task.pk,
        })
    return reverse('experiments:preview_task', kwargs={
        'pk': exp.pk, 'task_id': task.pk,
    })


def preview_next_url(exp, current_task=None):
    """
    Return the preview URL of the next task after current_task.
    current_task=None returns the URL for the first task in the experiment.
    Does not touch Visit records.
    """
    if current_task is None:
        first = exp.tasks.order_by('sort').first()
        if first is None:
            return reverse('experiments:preview_finish', kwargs={'pk': exp.pk})
        return _preview_url_for_task(exp, first)

    if current_task.sample_task_id:
        # Current task is a subtask - find next sibling subtask
        sample = current_task.sample_task
        next_sub = (
            sample.subtasks
            .filter(sort__gt=current_task.sort)
            .order_by('sort')
            .first()
        )
        if next_sub:
            return _preview_url_for_task(exp, next_sub)
        # No more subtasks - move to next top-level task after the sample
        next_top = exp.tasks.filter(sort__gt=sample.sort).order_by('sort').first()
        if next_top:
            return _preview_url_for_task(exp, next_top)
        return reverse('experiments:preview_finish', kwargs={'pk': exp.pk})

    # Current task is a top-level task
    next_top = exp.tasks.filter(sort__gt=current_task.sort).order_by('sort').first()
    if next_top:
        return _preview_url_for_task(exp, next_top)
    return reverse('experiments:preview_finish', kwargs={'pk': exp.pk})


def preview_sample_next_url(exp, sample):
    """Return the preview URL for the first subtask of a sample."""
    first_sub = sample.subtasks.order_by('sort').first()
    if first_sub:
        return _preview_url_for_task(exp, first_sub)
    # Sample has no subtasks - skip to next top-level task
    next_top = exp.tasks.filter(sort__gt=sample.sort).order_by('sort').first()
    if next_top:
        return _preview_url_for_task(exp, next_top)
    return reverse('experiments:preview_finish', kwargs={'pk': exp.pk})
