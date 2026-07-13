"""
next_task - port of Rails ResponsesHelper#next_task.

Finds the next unvisited task for a participant and returns the URL
to redirect them to. Handles random ordering within a group and
recurses up from SampleTask to Experiment at end of subtasks.
"""
import random as rng
from django.urls import reverse

from tasks.models import Task, SampleTask, QuestionTask, ListeningTask, ClickTask, IntermediateScreenTask
from experiments.models import Experiment
from .models import Visit


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
        # Finished this level - recurse up or finish
        if isinstance(taskable, SampleTask):
            parent_exp = taskable.experiment
            return next_task(parent_exp, participant_id, slug)
        return reverse('responses:finish', kwargs={'slug': slug, 'participant_id': participant_id})

    # Handle random flag: if the first unvisited task has random=True,
    # pick randomly among all consecutive random tasks in the unvisited list.
    if unvisited[0].random:
        random_group = [t for t in unvisited if t.random]
        chosen = rng.choice(random_group)
    else:
        chosen = unvisited[0]

    return _task_url(slug, participant_id, chosen)
