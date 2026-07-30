import rules
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from experiments.models import Experiment
from tasks.models import Task, SampleTask
from responses.helpers import (
    build_task_context,
    task_template_name,
    preview_next_url,
    preview_sample_next_url,
)


def _own_or_404(user, experiment):
    if not rules.has_perm('experiments.view_experiment', user, experiment):
        raise Http404


def _preview_ctx(exp):
    return {
        'preview': True,
        'preview_back_url': reverse('experiments:show', kwargs={'pk': exp.pk}),
    }


@method_decorator(login_required, name='dispatch')
class PreviewHomeView(View):
    def get(self, request, pk):
        exp = get_object_or_404(Experiment, pk=pk)
        _own_or_404(request.user, exp)
        ctx = {
            'experiment': exp,
            'start_url': reverse('experiments:preview_start', kwargs={'pk': pk}),
            **_preview_ctx(exp),
        }
        return render(request, 'responses/home.html', ctx)


@method_decorator(login_required, name='dispatch')
class PreviewStartView(View):
    def post(self, request, pk):
        exp = get_object_or_404(Experiment, pk=pk)
        _own_or_404(request.user, exp)
        return redirect(preview_next_url(exp, current_task=None))


@method_decorator(login_required, name='dispatch')
class PreviewSampleView(View):
    def get(self, request, pk, sample_id):
        exp = get_object_or_404(Experiment, pk=pk)
        _own_or_404(request.user, exp)
        task = get_object_or_404(Task, pk=sample_id)
        sample = task.get_specific()
        if not isinstance(sample, SampleTask):
            raise Http404
        ctx = {
            'experiment': exp,
            'sample': sample,
            'task': task,
            'next_url': preview_sample_next_url(exp, sample),
            **_preview_ctx(exp),
        }
        return render(request, 'responses/sample_intro.html', ctx)


@method_decorator(login_required, name='dispatch')
class PreviewTaskView(View):
    def get(self, request, pk, task_id):
        exp = get_object_or_404(Experiment, pk=pk)
        _own_or_404(request.user, exp)
        task = get_object_or_404(Task, pk=task_id)
        specific = task.get_specific()
        if specific is None:
            raise Http404

        sample = task.sample_task if task.sample_task_id else None
        audio_url = (
            reverse('experiments:preview_audio', kwargs={'pk': pk, 'sample_task_id': sample.pk})
            if sample else ''
        )
        next_url = preview_next_url(exp, current_task=task)
        submit_url = reverse('experiments:preview_task', kwargs={'pk': pk, 'task_id': task_id})

        ctx = build_task_context(
            exp, task, specific, sample, next_url,
            audio_url=audio_url,
            submit_url=submit_url,
            **_preview_ctx(exp),
        )
        return render(request, task_template_name(specific), ctx)

    def post(self, request, pk, task_id):
        # Question task submission in preview - skip saving, just navigate
        exp = get_object_or_404(Experiment, pk=pk)
        _own_or_404(request.user, exp)
        task = get_object_or_404(Task, pk=task_id)
        return redirect(preview_next_url(exp, current_task=task))


@method_decorator(login_required, name='dispatch')
class PreviewFinishView(View):
    def get(self, request, pk):
        exp = get_object_or_404(Experiment, pk=pk)
        _own_or_404(request.user, exp)
        ctx = {
            'experiment': exp,
            'response_slug': '',
            **_preview_ctx(exp),
        }
        return render(request, 'responses/finish.html', ctx)


@login_required
def preview_audio(request, pk, sample_task_id):
    exp = get_object_or_404(Experiment, pk=pk)
    _own_or_404(request.user, exp)
    sample = get_object_or_404(SampleTask, pk=sample_task_id)
    if sample.get_experiment_pk() != exp.pk:
        raise Http404
    if not sample.audio:
        raise Http404
    if getattr(settings, 'X_ACCEL_REDIRECT', False):
        response = HttpResponse()
        response['X-Accel-Redirect'] = f'/protected-media/{sample.audio.name}'
        response['Content-Type'] = 'audio/wav'
        return response
    return FileResponse(sample.audio.open('rb'), content_type='audio/wav')
