"""
Tests for authentication enforcement on researcher routes.

Covers: unauthenticated access redirects to login, researcher can only
        access their own experiments (ownership enforced with 404),
        participant routes require no login.
"""
import json

from django.test import TestCase

from responses.models import Visit
from .factories import make_user, make_experiment, make_question_task, make_question

LOGIN_URL = '/accounts/login/'


class TestResearcherRoutesRequireLogin(TestCase):
    def setUp(self):
        user = make_user()
        self.exp = make_experiment(user)

    def test_experiments_list_redirects_to_login(self):
        response = self.client.get('/experiments/')
        self.assertEqual(response.status_code, 302)
        self.assertIn(LOGIN_URL, response['Location'])

    def test_experiment_detail_redirects_to_login(self):
        response = self.client.get(f'/experiments/{self.exp.pk}/')
        self.assertEqual(response.status_code, 302)
        self.assertIn(LOGIN_URL, response['Location'])

    def test_experiment_edit_redirects_to_login(self):
        response = self.client.get(f'/experiments/{self.exp.pk}/edit/')
        self.assertEqual(response.status_code, 302)
        self.assertIn(LOGIN_URL, response['Location'])

    def test_experiment_new_redirects_to_login(self):
        response = self.client.get('/experiments/new/')
        self.assertEqual(response.status_code, 302)
        self.assertIn(LOGIN_URL, response['Location'])


class TestResearcherOwnership(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.other = make_user()
        self.exp = make_experiment(self.owner)

    def test_owner_can_view_own_experiment(self):
        self.client.force_login(self.owner)
        response = self.client.get(f'/experiments/{self.exp.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_other_researcher_gets_404_on_experiment_detail(self):
        self.client.force_login(self.other)
        response = self.client.get(f'/experiments/{self.exp.pk}/')
        self.assertEqual(response.status_code, 404)

    def test_other_researcher_gets_404_on_experiment_edit(self):
        self.client.force_login(self.other)
        response = self.client.get(f'/experiments/{self.exp.pk}/edit/')
        self.assertEqual(response.status_code, 404)

    def test_other_researcher_gets_404_on_download(self):
        self.client.force_login(self.other)
        response = self.client.get(f'/experiments/{self.exp.pk}/download/')
        self.assertEqual(response.status_code, 404)

    def test_experiment_list_only_shows_own_experiments(self):
        other_exp = make_experiment(self.other, name='Other Exp')
        self.client.force_login(self.owner)
        response = self.client.get('/experiments/')
        self.assertEqual(response.status_code, 200)
        experiments = list(response.context['experiments'])
        pks = [e.pk for e in experiments]
        self.assertIn(self.exp.pk, pks)
        self.assertNotIn(other_exp.pk, pks)


class TestTaskOwnership(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.other = make_user()
        self.exp = make_experiment(self.owner)
        self.qt = make_question_task(name='Q1', sort=1, experiment=self.exp)

    def test_owner_can_edit_own_task(self):
        self.client.force_login(self.owner)
        response = self.client.get(f'/tasks/question-task/{self.qt.pk}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_other_researcher_gets_404_on_task_edit(self):
        self.client.force_login(self.other)
        response = self.client.get(f'/tasks/question-task/{self.qt.pk}/edit/')
        self.assertEqual(response.status_code, 404)


class TestParticipantRoutesRequireNoLogin(TestCase):
    def setUp(self):
        user = make_user()
        self.exp = make_experiment(user, complete=True)
        self.qt = make_question_task(name='Q1', sort=1, experiment=self.exp)
        Visit.objects.create(participant_id=1, task_id=self.qt.pk, visited=False)

    def test_home_accessible_anonymously(self):
        response = self.client.get(f'/{self.exp.slug}/home/')
        self.assertEqual(response.status_code, 200)

    def test_task_view_accessible_anonymously(self):
        response = self.client.get(f'/{self.exp.slug}/1/questiontask/{self.qt.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_click_endpoint_accessible_anonymously(self):
        response = self.client.post(
            '/click-responses/',
            json.dumps([]),
            content_type='application/json',
        )
        # Empty list → 200 OK (no auth check when list is empty)
        self.assertEqual(response.status_code, 200)
