"""
Integration tests for the unauthenticated participant flow.

Covers: home view (published / unpublished), start view (consent enforcement,
        participant_id assignment, Visit creation), task view (mark visited),
        question submit (save response, required enforcement), finish view.
"""
from django.test import TestCase, Client
from django.urls import reverse

from responses.models import Visit, ParticipantId, Response

from .factories import make_user, make_experiment, make_question_task, make_question, make_sample_task


class TestExperimentHomeView(TestCase):
    def test_home_returns_200_for_published_experiment(self):
        user = make_user()
        exp = make_experiment(user, complete=True)
        response = self.client.get(f'/{exp.slug}/home/')
        self.assertEqual(response.status_code, 200)

    def test_home_returns_404_for_unpublished_experiment(self):
        user = make_user()
        exp = make_experiment(user, complete=False)
        response = self.client.get(f'/{exp.slug}/home/')
        self.assertEqual(response.status_code, 404)

    def test_home_accessible_without_login(self):
        # Participant routes must never require authentication
        user = make_user()
        exp = make_experiment(user, complete=True)
        # No client.force_login() call - anonymous request
        response = self.client.get(f'/{exp.slug}/home/')
        self.assertNotEqual(response.status_code, 302)  # must not redirect to login


class TestExperimentStartView(TestCase):
    def setUp(self):
        user = make_user()
        self.exp = make_experiment(user, complete=True)
        self.qt = make_question_task(name='Q1', sort=1, experiment=self.exp)

    def test_start_without_consent_rerenders_with_error(self):
        response = self.client.post(f'/{self.exp.slug}/start/', {'email': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You must accept')

    def test_start_with_consent_creates_participant_id_record(self):
        self.client.post(
            f'/{self.exp.slug}/start/',
            {'consent': 'on', 'email': 'p@example.com'},
        )
        pid_rec = ParticipantId.objects.filter(experiment=self.exp).first()
        self.assertIsNotNone(pid_rec)
        self.assertEqual(pid_rec.participant_id, 1)
        self.assertIsNotNone(pid_rec.slug)

    def test_start_creates_visit_rows_for_all_tasks(self):
        qt2 = make_question_task(name='Q2', sort=2, experiment=self.exp)
        self.client.post(f'/{self.exp.slug}/start/', {'consent': 'on', 'email': ''})
        self.assertTrue(Visit.objects.filter(participant_id=1, task_id=self.qt.pk).exists())
        self.assertTrue(Visit.objects.filter(participant_id=1, task_id=qt2.pk).exists())

    def test_start_redirects_to_first_task(self):
        response = self.client.post(
            f'/{self.exp.slug}/start/', {'consent': 'on', 'email': ''},
        )
        expected_url = reverse('responses:task_view', kwargs={
            'slug': self.exp.slug,
            'participant_id': 1,
            'task_type': 'questiontask',
            'task_id': self.qt.pk,
        })
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)

    def test_start_increments_participant_id(self):
        Client().post(f'/{self.exp.slug}/start/', {'consent': 'on', 'email': ''})
        Client().post(f'/{self.exp.slug}/start/', {'consent': 'on', 'email': ''})

        pids = sorted(
            ParticipantId.objects
            .filter(experiment=self.exp)
            .values_list('participant_id', flat=True)
        )
        self.assertEqual(pids, [1, 2])

    def test_start_on_incomplete_experiment_returns_404(self):
        user = make_user()
        exp = make_experiment(user, complete=False)
        response = self.client.post(f'/{exp.slug}/start/', {'consent': 'on', 'email': ''})
        self.assertEqual(response.status_code, 404)


class TestTaskView(TestCase):
    def setUp(self):
        user = make_user()
        self.exp = make_experiment(user, complete=True)
        self.qt = make_question_task(name='Q1', sort=1, experiment=self.exp)
        self.pid = 3
        Visit.objects.create(participant_id=self.pid, task_id=self.qt.pk, visited=False)

    def _url(self):
        return f'/{self.exp.slug}/{self.pid}/questiontask/{self.qt.pk}/'

    def test_task_view_returns_200(self):
        self.assertEqual(self.client.get(self._url()).status_code, 200)

    def test_task_view_marks_visit_as_visited(self):
        self.client.get(self._url())
        self.assertTrue(
            Visit.objects.get(participant_id=self.pid, task_id=self.qt.pk).visited
        )

    def test_task_view_404_for_nonexistent_task(self):
        response = self.client.get(f'/{self.exp.slug}/{self.pid}/questiontask/99999/')
        self.assertEqual(response.status_code, 404)

    def test_task_view_accessible_without_login(self):
        # Must not redirect to login
        self.assertNotEqual(self.client.get(self._url()).status_code, 302)


class TestTaskSubmitView(TestCase):
    def setUp(self):
        user = make_user()
        self.exp = make_experiment(user, complete=True)
        self.qt = make_question_task(name='Q1', sort=1, experiment=self.exp)
        self.q = make_question(self.qt, prompt='How was it?', sort=1, required=False)
        self.pid = 8
        Visit.objects.create(participant_id=self.pid, task_id=self.qt.pk, visited=True)

    def _url(self):
        return f'/{self.exp.slug}/{self.pid}/questiontask/{self.qt.pk}/submit/'

    def test_submit_saves_response(self):
        self.client.post(self._url(), {f'question_{self.q.pk}': 'Great!'})
        r = Response.objects.get(participant_id=self.pid, question=self.q)
        self.assertEqual(r.answer, 'Great!')

    def test_submit_redirects_after_save(self):
        response = self.client.post(self._url(), {f'question_{self.q.pk}': 'Great!'})
        self.assertEqual(response.status_code, 302)

    def test_required_question_empty_rerenders_with_error(self):
        self.q.required = True
        self.q.save(update_fields=['required'])

        response = self.client.post(self._url(), {f'question_{self.q.pk}': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'required')
        self.assertEqual(Response.objects.count(), 0)

    def test_required_question_empty_rerenders_questions(self):
        self.q.required = True
        self.q.save(update_fields=['required'])

        response = self.client.post(self._url(), {f'question_{self.q.pk}': ''})
        # Template must render questions (bug fix: questions was missing from error context)
        self.assertContains(response, 'How was it?')

    def test_optional_question_blank_answer_saves_empty_string(self):
        self.client.post(self._url(), {f'question_{self.q.pk}': ''})
        r = Response.objects.get(participant_id=self.pid, question=self.q)
        self.assertEqual(r.answer, '')


class TestServeAudio(TestCase):
    def test_nonexistent_sample_returns_404(self):
        response = self.client.get('/audio/99999/')
        self.assertEqual(response.status_code, 404)

    def test_unpublished_experiment_returns_404(self):
        user = make_user()
        exp = make_experiment(user, complete=False)
        sample = make_sample_task(exp)
        response = self.client.get(f'/audio/{sample.pk}/')
        self.assertEqual(response.status_code, 404)

    def test_published_experiment_without_audio_returns_404(self):
        user = make_user()
        exp = make_experiment(user, complete=True)
        sample = make_sample_task(exp)
        response = self.client.get(f'/audio/{sample.pk}/')
        self.assertEqual(response.status_code, 404)

    def test_audio_endpoint_accessible_without_login(self):
        user = make_user()
        exp = make_experiment(user, complete=False)
        sample = make_sample_task(exp)
        response = self.client.get(f'/audio/{sample.pk}/')
        self.assertNotEqual(response.status_code, 302)


class TestFinishView(TestCase):
    def test_finish_returns_200(self):
        user = make_user()
        exp = make_experiment(user, complete=True)
        pid = 1
        pid_rec = ParticipantId(experiment=exp, participant_id=pid)
        pid_rec.email = ''
        pid_rec.save()
        response = self.client.get(f'/{exp.slug}/{pid}/finish/')
        self.assertEqual(response.status_code, 200)
