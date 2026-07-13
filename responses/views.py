import json
import urllib.parse
import urllib.request

from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.http import Http404, HttpResponse, FileResponse, JsonResponse
from django.views import View
from django.db import transaction
from django.db.models import Max

from experiments.models import Experiment
from tasks.models import Task, SampleTask, QuestionTask, ListeningTask, ClickTask, IntermediateScreenTask
from .models import Visit, ParticipantId, Response, ClickResponse
from .helpers import next_task


# ── Experiment home ─────────────────────────────────────────────────────────

class ExperimentHomeView(View):
    def get(self, request, slug):
        exp = get_object_or_404(Experiment, slug=slug, complete=True)
        return render(request, 'responses/home.html', {'experiment': exp})


class ExperimentStartView(View):
    def post(self, request, slug):
        exp = get_object_or_404(Experiment, slug=slug, complete=True)

        # Validate consent checkbox (template field name is 'consent')
        if not request.POST.get('consent'):
            return render(request, 'responses/home.html', {
                'experiment': exp,
                'error': 'You must accept the terms to continue.',
            })

        # reCAPTCHA validation - skip if no private key configured (dev without key)
        if getattr(settings, 'RECAPTCHA_PRIVATE_KEY', ''):
            captcha_response = request.POST.get('g-recaptcha-response', '')
            if not captcha_response:
                return render(request, 'responses/home.html', {
                    'experiment': exp, 'error': 'Please complete the reCAPTCHA.',
                })
            # Verify token with Google's API - a non-empty token is not sufficient
            try:
                _payload = urllib.parse.urlencode({
                    'secret': settings.RECAPTCHA_PRIVATE_KEY,
                    'response': captcha_response,
                    'remoteip': request.META.get('REMOTE_ADDR', ''),
                }).encode()
                with urllib.request.urlopen(
                    'https://www.google.com/recaptcha/api/siteverify', _payload, timeout=5
                ) as _resp:
                    _result = json.loads(_resp.read())
            except Exception:
                _result = {}
            if not _result.get('success'):
                return render(request, 'responses/home.html', {
                    'experiment': exp, 'error': 'reCAPTCHA validation failed. Please try again.',
                })

        email = request.POST.get('email', '').strip()

        with transaction.atomic():
            # Lock Experiment row to serialize participant_id assignment.
            # Locking Visit rows doesn't work when no visits exist yet (empty table → nothing to lock).
            exp = Experiment.objects.select_for_update().get(pk=exp.pk)
            top_level_tasks = list(exp.tasks.order_by('sort'))
            max_pid = (
                ParticipantId.objects
                .filter(experiment=exp)
                .aggregate(m=Max('participant_id'))['m']
            ) or 0
            participant_id = max_pid + 1

            # Create Visit rows for all top-level tasks
            Visit.objects.bulk_create([
                Visit(participant_id=participant_id, task=t, visited=False)
                for t in top_level_tasks
            ])

            # Record participant email (encrypted)
            pid_record = ParticipantId(experiment=exp, participant_id=participant_id)
            pid_record.email = email
            pid_record.save()

        url = next_task(exp, participant_id, slug)
        return redirect(url)


# ── Sample intro ────────────────────────────────────────────────────────────

class SampleIntroView(View):
    def get(self, request, slug, participant_id, sample_id):
        exp = get_object_or_404(Experiment, slug=slug, complete=True)
        task = get_object_or_404(Task, pk=sample_id)
        sample = task.get_specific()
        if not isinstance(sample, SampleTask):
            raise Http404

        # Create Visit rows for subtasks if not already created
        subtasks = list(sample.subtasks.order_by('sort'))
        existing = set(
            Visit.objects
            .filter(participant_id=participant_id, task__in=subtasks)
            .values_list('task_id', flat=True)
        )
        new_visits = [
            Visit(participant_id=participant_id, task=st, visited=False)
            for st in subtasks if st.pk not in existing
        ]
        if new_visits:
            Visit.objects.bulk_create(new_visits)

        next_url = next_task(sample, participant_id, slug)
        return render(request, 'responses/sample_intro.html', {
            'experiment': exp,
            'sample': sample,
            'task': task,
            'participant_id': participant_id,
            'slug': slug,
            'next_url': next_url,
        })


# ── Task view ───────────────────────────────────────────────────────────────

class TaskView(View):
    def get(self, request, slug, participant_id, task_type, task_id):
        exp = get_object_or_404(Experiment, slug=slug, complete=True)
        task = get_object_or_404(Task, pk=task_id)
        specific = task.get_specific()
        if specific is None:
            raise Http404

        # Mark this task visited
        Visit.objects.filter(participant_id=participant_id, task=task).update(visited=True)

        # Load transcript content for SampleTask-owned tasks (for click task JS)
        transcript_content = ''
        sample = None
        if task.sample_task_id:
            sample = task.sample_task
            if sample.transcript:
                try:
                    transcript_content = sample.transcript.read().decode('utf-8')
                    sample.transcript.seek(0)
                except Exception:
                    transcript_content = ''

        # Determine next URL (for JS to navigate after click task submission)
        taskable = exp if task.experiment_id else sample
        next_url = next_task(taskable, participant_id, slug)

        # Build question list for QuestionTask templates
        questions = list(specific.questions.order_by('sort')) if isinstance(specific, QuestionTask) else []

        ctx = {
            'experiment': exp,
            'task': task,
            'specific': specific,
            # sample / sample_task aliases (templates use both)
            'sample': sample,
            'sample_task': sample,
            'participant_id': participant_id,
            'slug': slug,
            # transcript aliases (click_task.html uses transcript_xml)
            'transcript_content': transcript_content,
            'transcript_xml': transcript_content,
            'next_url': next_url,
            'questions': questions,
            # calibration flag for click task template
            'is_calibration': sample.calibration if sample else False,
        }
        template_map = {
            'QuestionTask': 'responses/tasks/question_task.html',
            'SampleTask': 'responses/tasks/sample_task.html',
            'ListeningTask': 'responses/tasks/listening_task.html',
            'ClickTask': 'responses/tasks/click_task.html',
            'IntermediateScreenTask': 'responses/tasks/intermediate_screen_task.html',
        }
        template = template_map.get(type(specific).__name__, 'responses/tasks/question_task.html')
        return render(request, template, ctx)


# ── Task submit ─────────────────────────────────────────────────────────────

class TaskSubmitView(View):
    def post(self, request, slug, participant_id, task_type, task_id):
        exp = get_object_or_404(Experiment, slug=slug, complete=True)
        task = get_object_or_404(Task, pk=task_id)
        specific = task.get_specific()

        if isinstance(specific, QuestionTask):
            errors = []
            for question in specific.questions.order_by('sort'):
                answer = request.POST.get(f'question_{question.pk}', '').strip()
                if question.required and not answer:
                    errors.append(f'"{question.prompt}" is required.')
                    continue
                resp = Response(participant_id=participant_id, question=question)
                resp.answer = answer
                resp.save()

            if errors:
                # Re-render with errors - rebuild context same as TaskView.get
                sample = task.sample_task if task.sample_task_id else None
                transcript_content = ''
                if sample and sample.transcript:
                    try:
                        transcript_content = sample.transcript.read().decode('utf-8')
                    except Exception:
                        pass
                taskable = exp if task.experiment_id else sample
                next_url = next_task(taskable, participant_id, slug)
                return render(request, 'responses/tasks/question_task.html', {
                    'experiment': exp, 'task': task, 'specific': specific,
                    'participant_id': participant_id, 'slug': slug,
                    'transcript_content': transcript_content, 'next_url': next_url,
                    'errors': errors, 'submitted_data': request.POST,
                    'questions': list(specific.questions.order_by('sort')),
                })

        taskable = exp if task.experiment_id else task.sample_task
        url = next_task(taskable, participant_id, slug)
        return redirect(url)


# ── Finish ──────────────────────────────────────────────────────────────────

class FinishView(View):
    def get(self, request, slug, participant_id):
        exp = get_object_or_404(Experiment, slug=slug, complete=True)
        pid_record = ParticipantId.objects.filter(
            experiment=exp, participant_id=participant_id
        ).first()
        response_slug = pid_record.slug if pid_record else ''
        return render(request, 'responses/finish.html', {
            'experiment': exp,
            'response_slug': response_slug,
        })


# ── Click response XHR ──────────────────────────────────────────────────────

class ClickResponseView(View):
    """Receives JSON array of click responses from the JS click task."""

    def post(self, request):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'invalid json'}, status=400)

        if not isinstance(data, list):
            return JsonResponse({'error': 'expected array'}, status=400)

        to_create = []
        for item in data:
            try:
                ct = get_object_or_404(ClickTask, pk=item['click_task_id'])
                pid = item['participant_id']
                # Verify this participant actually has a Visit for this task
                if not Visit.objects.filter(participant_id=pid, task_id=ct.pk).exists():
                    return JsonResponse({'error': 'unauthorized'}, status=403)
                cr = ClickResponse(
                    participant_id=pid,
                    click_task=ct,
                    time=item.get('time'),
                    no_clicks_explanation=bool(item.get('no_clicks_explanation', False)),
                    from_checkbox=bool(item.get('from_checkbox', False)),
                )
                cr.answer = item.get('answer', '')
                to_create.append(cr)
            except (KeyError, TypeError):
                return JsonResponse({'error': 'malformed item'}, status=400)

        for cr in to_create:
            cr.save()

        return JsonResponse({'ok': True})


# ── Audio serve (Nginx X-Accel-Redirect) ────────────────────────────────────

def serve_audio(request, sample_task_id):
    sample = get_object_or_404(SampleTask, pk=sample_task_id)

    # Refuse to serve audio for unpublished experiments - prevents enumeration of stimuli
    if not Experiment.objects.filter(pk=sample.get_experiment_pk(), complete=True).exists():
        raise Http404

    if not sample.audio:
        raise Http404

    if getattr(settings, 'X_ACCEL_REDIRECT', False):
        response = HttpResponse()
        response['X-Accel-Redirect'] = f'/protected-media/{sample.audio.name}'
        response['Content-Type'] = 'audio/wav'
        return response

    # Development: serve directly
    return FileResponse(sample.audio.open('rb'), content_type='audio/wav')
