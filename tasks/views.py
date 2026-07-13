import rules
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.shortcuts import get_object_or_404, redirect, render
from django.http import Http404, JsonResponse
from django.db import transaction
from django.db.models import Max

from experiments.models import Experiment
from .models import (
    Task, QuestionTask, SampleTask, ListeningTask, ClickTask,
    IntermediateScreenTask, Question, Option, Scale,
    QUESTION_TYPE_CHOICES, QUESTION_TYPE_RATING, QUESTION_DEFAULT_PROMPTS,
)
from .forms import (
    QuestionTaskForm, SampleTaskForm, ListeningTaskForm, ClickTaskForm,
    IntermediateScreenTaskForm, AudioUploadForm, TranscriptUploadForm,
    QuestionForm, QuestionPromptForm, OptionForm, ScaleForm,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _resolve_taskable(taskable_type, taskable_id, user):
    """Return (taskable_object, experiment) or raise Http404."""
    if taskable_type == 'experiment':
        exp = get_object_or_404(Experiment, pk=taskable_id)
        if exp.user_id != user.pk:
            raise Http404
        return exp, exp
    elif taskable_type == 'sampletask':
        st = get_object_or_404(SampleTask, pk=taskable_id)
        if not rules.has_perm('tasks.change_task', user, st):
            raise Http404
        return st, st.experiment
    raise Http404


def _check_task(user, task):
    if not rules.has_perm('tasks.change_task', user, task):
        raise Http404


def _next_sort(taskable):
    if isinstance(taskable, Experiment):
        return (taskable.tasks.aggregate(m=Max('sort'))['m'] or 0) + 1
    return (taskable.subtasks.aggregate(m=Max('sort'))['m'] or 0) + 1


def _create_with_base(taskable, specific_class, specific_kwargs, name):
    """Atomically create Task + MTI subclass."""
    with transaction.atomic():
        sort = _next_sort(taskable)
        if isinstance(taskable, Experiment):
            base_kwargs = dict(name=name, experiment=taskable, sort=sort)
        else:
            base_kwargs = dict(name=name, sample_task=taskable, sort=sort)
        specific = specific_class(**base_kwargs, **specific_kwargs)
        specific.save()
    return specific


# ── Generic task-type views ─────────────────────────────────────────────────

def _task_new(request, taskable_type, taskable_id, form_class, template):
    taskable, _ = _resolve_taskable(taskable_type, taskable_id, request.user)
    form = form_class()
    return render(request, template, {'form': form, 'taskable': taskable,
                                       'taskable_type': taskable_type,
                                       'taskable_id': taskable_id})


def _task_create(request, taskable_type, taskable_id, specific_class, form_class,
                 extra_fields, redirect_view):
    taskable, exp = _resolve_taskable(taskable_type, taskable_id, request.user)
    form = form_class(request.POST)
    if form.is_valid():
        kwargs = {f: form.cleaned_data[f] for f in extra_fields if f in form.cleaned_data}
        specific = _create_with_base(taskable, specific_class, kwargs, form.cleaned_data['name'])
        messages.success(request, 'Task created.')
        return redirect('experiments:show', pk=exp.pk)
    return render(request, f'tasks/{redirect_view}_new.html',
                  {'form': form, 'taskable': taskable})


def _task_edit(request, pk, model_class, form_class, template):
    task = get_object_or_404(model_class, pk=pk)
    _check_task(request.user, task)
    form = form_class(instance=task)
    owning_experiment = task.experiment or task.sample_task.experiment
    return render(request, template, {'form': form, 'task': task,
                                      'owning_experiment': owning_experiment})


def _task_update(request, pk, model_class, form_class, template):
    task = get_object_or_404(model_class, pk=pk)
    _check_task(request.user, task)
    form = form_class(request.POST, instance=task)
    owning_experiment = task.experiment or task.sample_task.experiment
    if form.is_valid():
        form.save()
        messages.success(request, 'Saved.')
        return redirect('experiments:show', pk=owning_experiment.pk)
    return render(request, template, {'form': form, 'task': task,
                                      'owning_experiment': owning_experiment})


def _task_delete(request, pk, model_class):
    task = get_object_or_404(model_class, pk=pk)
    _check_task(request.user, task)
    exp = task.experiment or task.sample_task.experiment
    if request.method == 'POST':
        task.delete()
    return redirect('experiments:show', pk=exp.pk)


# ── QuestionTask views ──────────────────────────────────────────────────────

@login_required
def question_task_new(request, taskable_type, taskable_id):
    return _task_new(request, taskable_type, taskable_id, QuestionTaskForm,
                     'tasks/question_task_new.html')


@login_required
def question_task_create(request, taskable_type, taskable_id):
    return _task_create(request, taskable_type, taskable_id, QuestionTask,
                        QuestionTaskForm, [], 'question_task')


def _question_task_context(task):
    owning_exp = task.experiment if task.experiment_id else task.sample_task.experiment
    return {
        'task': task,
        'question_type_choices': QUESTION_TYPE_CHOICES,
        'owning_experiment': owning_exp,
    }


@login_required
def question_task_edit(request, pk):
    task = get_object_or_404(QuestionTask, pk=pk)
    _check_task(request.user, task)
    ctx = _question_task_context(task)
    ctx['form'] = QuestionTaskForm(instance=task)
    return render(request, 'tasks/question_task_edit.html', ctx)


@login_required
def question_task_update(request, pk):
    task = get_object_or_404(QuestionTask, pk=pk)
    _check_task(request.user, task)
    form = QuestionTaskForm(request.POST, instance=task)
    if form.is_valid():
        form.save()
        messages.success(request, 'Saved.')
        return redirect('tasks:question_task_edit', pk=task.pk)
    ctx = _question_task_context(task)
    ctx['form'] = form
    return render(request, 'tasks/question_task_edit.html', ctx)


@login_required
def question_task_delete(request, pk):
    return _task_delete(request, pk, QuestionTask)


# ── SampleTask views ────────────────────────────────────────────────────────

@login_required
def sample_task_new(request, taskable_type, taskable_id):
    return _task_new(request, taskable_type, taskable_id, SampleTaskForm,
                     'tasks/sample_task_new.html')


@login_required
def sample_task_create(request, taskable_type, taskable_id):
    return _task_create(request, taskable_type, taskable_id, SampleTask,
                        SampleTaskForm, ['calibration'], 'sample_task')


@login_required
def sample_task_edit(request, pk):
    return _task_edit(request, pk, SampleTask, SampleTaskForm, 'tasks/sample_task_edit.html')


@login_required
def sample_task_update(request, pk):
    return _task_update(request, pk, SampleTask, SampleTaskForm, 'tasks/sample_task_edit.html')


@login_required
def sample_task_delete(request, pk):
    return _task_delete(request, pk, SampleTask)


@login_required
def audio_upload(request, pk):
    st = get_object_or_404(SampleTask, pk=pk)
    _check_task(request.user, st)
    if request.method == 'POST':
        form = AudioUploadForm(request.POST, request.FILES)
        if form.is_valid():
            if st.audio:
                st.audio.delete(save=False)
            st.audio = form.cleaned_data['audio']
            st.save(update_fields=['audio'])
            messages.success(request, 'Audio uploaded.')
    return redirect('tasks:sample_task_edit', pk=pk)


@login_required
def audio_delete(request, pk):
    st = get_object_or_404(SampleTask, pk=pk)
    _check_task(request.user, st)
    if request.method == 'POST' and st.audio:
        st.audio.delete(save=False)
        st.audio = None
        st.save(update_fields=['audio'])
    return redirect('tasks:sample_task_edit', pk=pk)


@login_required
def transcript_upload(request, pk):
    st = get_object_or_404(SampleTask, pk=pk)
    _check_task(request.user, st)
    if request.method == 'POST':
        form = TranscriptUploadForm(request.POST, request.FILES)
        if form.is_valid():
            if st.transcript:
                st.transcript.delete(save=False)
            st.transcript = form.cleaned_data['transcript']
            st.save(update_fields=['transcript'])
            messages.success(request, 'Transcript uploaded.')
    return redirect('tasks:sample_task_edit', pk=pk)


@login_required
def transcript_delete(request, pk):
    st = get_object_or_404(SampleTask, pk=pk)
    _check_task(request.user, st)
    if request.method == 'POST' and st.transcript:
        st.transcript.delete(save=False)
        st.transcript = None
        st.save(update_fields=['transcript'])
    return redirect('tasks:sample_task_edit', pk=pk)


@login_required
def calibration_toggle(request, pk):
    st = get_object_or_404(SampleTask, pk=pk)
    _check_task(request.user, st)
    if request.method == 'POST':
        st.calibration = not st.calibration
        st.save(update_fields=['calibration'])
    return redirect('tasks:sample_task_edit', pk=pk)


# ── ListeningTask views ─────────────────────────────────────────────────────

@login_required
def listening_task_new(request, taskable_type, taskable_id):
    return _task_new(request, taskable_type, taskable_id, ListeningTaskForm,
                     'tasks/listening_task_new.html')


@login_required
def listening_task_create(request, taskable_type, taskable_id):
    return _task_create(request, taskable_type, taskable_id, ListeningTask,
                        ListeningTaskForm, ['listens'], 'listening_task')


@login_required
def listening_task_edit(request, pk):
    return _task_edit(request, pk, ListeningTask, ListeningTaskForm, 'tasks/listening_task_edit.html')


@login_required
def listening_task_update(request, pk):
    return _task_update(request, pk, ListeningTask, ListeningTaskForm, 'tasks/listening_task_edit.html')


@login_required
def listening_task_delete(request, pk):
    return _task_delete(request, pk, ListeningTask)


# ── ClickTask views ─────────────────────────────────────────────────────────

@login_required
def click_task_new(request, taskable_type, taskable_id):
    return _task_new(request, taskable_type, taskable_id, ClickTaskForm,
                     'tasks/click_task_new.html')


@login_required
def click_task_create(request, taskable_type, taskable_id):
    return _task_create(request, taskable_type, taskable_id, ClickTask,
                        ClickTaskForm, ['prompt', 'explanation_prompt'], 'click_task')


@login_required
def click_task_edit(request, pk):
    return _task_edit(request, pk, ClickTask, ClickTaskForm, 'tasks/click_task_edit.html')


@login_required
def click_task_update(request, pk):
    return _task_update(request, pk, ClickTask, ClickTaskForm, 'tasks/click_task_edit.html')


@login_required
def click_task_delete(request, pk):
    return _task_delete(request, pk, ClickTask)


# ── IntermediateScreenTask views ────────────────────────────────────────────

@login_required
def intermediate_screen_new(request, taskable_type, taskable_id):
    return _task_new(request, taskable_type, taskable_id, IntermediateScreenTaskForm,
                     'tasks/intermediate_screen_new.html')


@login_required
def intermediate_screen_create(request, taskable_type, taskable_id):
    return _task_create(request, taskable_type, taskable_id, IntermediateScreenTask,
                        IntermediateScreenTaskForm, ['message'], 'intermediate_screen')


@login_required
def intermediate_screen_edit(request, pk):
    return _task_edit(request, pk, IntermediateScreenTask, IntermediateScreenTaskForm,
                      'tasks/intermediate_screen_edit.html')


@login_required
def intermediate_screen_update(request, pk):
    return _task_update(request, pk, IntermediateScreenTask, IntermediateScreenTaskForm,
                        'tasks/intermediate_screen_edit.html')


@login_required
def intermediate_screen_delete(request, pk):
    return _task_delete(request, pk, IntermediateScreenTask)


# ── Task common ─────────────────────────────────────────────────────────────

@login_required
def task_random(request, pk):
    task = get_object_or_404(Task, pk=pk)
    _check_task(request.user, task)
    if request.method == 'POST':
        task.random = not task.random
        task.save(update_fields=['random'])
    return JsonResponse({'random': task.random})


# ── Question views ──────────────────────────────────────────────────────────

@login_required
def question_create(request, qt_pk):
    qt = get_object_or_404(QuestionTask, pk=qt_pk)
    _check_task(request.user, qt)
    if request.method == 'POST':
        q_type = request.POST.get('question_type', 'text')
        if q_type in dict(QUESTION_TYPE_CHOICES):
            max_sort = qt.questions.aggregate(m=Max('sort'))['m'] or 0
            q = Question.objects.create(
                question_task=qt,
                question_type=q_type,
                prompt=QUESTION_DEFAULT_PROMPTS.get(q_type, ''),
                sort=max_sort + 1,
            )
            if q_type == QUESTION_TYPE_RATING:
                Scale.objects.create(question=q, bins=7, low='', high='')
    return redirect('tasks:question_task_edit', pk=qt_pk)


@login_required
def question_update(request, pk):
    q = get_object_or_404(Question, pk=pk)
    if not rules.has_perm('tasks.change_question', request.user, q):
        raise Http404
    if request.method == 'POST':
        form = QuestionPromptForm(request.POST, instance=q)
        if form.is_valid():
            form.save()
            messages.success(request, 'Saved.')
    return redirect('tasks:question_task_edit', pk=q.question_task_id)


@login_required
def question_delete(request, pk):
    q = get_object_or_404(Question, pk=pk)
    if not rules.has_perm('tasks.delete_question', request.user, q):
        raise Http404
    qt_pk = q.question_task_id
    if request.method == 'POST':
        q.delete()
    return redirect('tasks:question_task_edit', pk=qt_pk)


@login_required
def scale_update(request, pk):
    q = get_object_or_404(Question, pk=pk)
    if not rules.has_perm('tasks.change_question', request.user, q):
        raise Http404
    scale, _ = Scale.objects.get_or_create(question=q, defaults={'bins': 5})
    if request.method == 'POST':
        form = ScaleForm(request.POST, instance=scale)
        if form.is_valid():
            form.save()
            messages.success(request, 'Saved.')
    return redirect('tasks:question_task_edit', pk=q.question_task_id)


# ── Option views ────────────────────────────────────────────────────────────

@login_required
def option_create(request, q_pk):
    q = get_object_or_404(Question, pk=q_pk)
    if not rules.has_perm('tasks.change_question', request.user, q):
        raise Http404
    if request.method == 'POST':
        form = OptionForm(request.POST)
        if form.is_valid():
            opt = form.save(commit=False)
            opt.question = q
            opt.save()
    return redirect('tasks:question_task_edit', pk=q.question_task_id)


@login_required
def option_delete(request, pk):
    opt = get_object_or_404(Option, pk=pk)
    if not rules.has_perm('tasks.delete_option', request.user, opt):
        raise Http404
    qt_pk = opt.question.question_task_id
    if request.method == 'POST':
        opt.delete()
    return redirect('tasks:question_task_edit', pk=qt_pk)
