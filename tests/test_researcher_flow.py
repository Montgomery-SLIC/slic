"""
Tests for the full researcher CRUD flow: experiments, tasks, questions, admin.
All mutation endpoints require login; ownership is enforced with 404.
"""
from django.test import TestCase

from experiments.models import Experiment
from accounts.models import ResearcherInvitation
from tasks.models import (
    QuestionTask, SampleTask, ClickTask,
    ListeningTask, IntermediateScreenTask, Question, Scale,
)

from .factories import (
    make_user, make_experiment, make_question_task,
    make_sample_task, make_click_task, make_listening_task, make_question,
)

LOGIN_URL = '/accounts/login/'


# ── Experiment creation ──────────────────────────────────────────────────────

class TestExperimentCreate(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_authenticated_post_creates_experiment(self):
        self.client.force_login(self.user)
        before = Experiment.objects.count()
        self.client.post('/experiments/new/', {'name': 'My Exp', 'description': ''})
        self.assertEqual(Experiment.objects.count(), before + 1)

    def test_create_redirects_to_show_page(self):
        self.client.force_login(self.user)
        response = self.client.post('/experiments/new/', {'name': 'My Exp', 'description': ''})
        exp = Experiment.objects.get(name='My Exp')
        self.assertRedirects(response, f'/experiments/{exp.pk}/')

    def test_blank_name_rerenders_form(self):
        self.client.force_login(self.user)
        before = Experiment.objects.count()
        response = self.client.post('/experiments/new/', {'name': '', 'description': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Experiment.objects.count(), before)

    def test_unauthenticated_post_redirects_to_login(self):
        response = self.client.post('/experiments/new/', {'name': 'My Exp', 'description': ''})
        self.assertEqual(response.status_code, 302)
        self.assertIn(LOGIN_URL, response['Location'])


# ── Experiment editing ───────────────────────────────────────────────────────

class TestExperimentEdit(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.other = make_user()
        self.exp = make_experiment(self.owner, name='Original')

    def test_owner_can_get_edit_page(self):
        self.client.force_login(self.owner)
        response = self.client.get(f'/experiments/{self.exp.pk}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_owner_post_updates_name(self):
        self.client.force_login(self.owner)
        self.client.post(f'/experiments/{self.exp.pk}/edit/', {'name': 'Updated', 'description': ''})
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.name, 'Updated')

    def test_owner_update_redirects_to_show(self):
        self.client.force_login(self.owner)
        response = self.client.post(f'/experiments/{self.exp.pk}/edit/', {'name': 'Updated', 'description': ''})
        self.assertRedirects(response, f'/experiments/{self.exp.pk}/')

    def test_non_owner_post_returns_404(self):
        self.client.force_login(self.other)
        response = self.client.post(f'/experiments/{self.exp.pk}/edit/', {'name': 'Stolen', 'description': ''})
        self.assertEqual(response.status_code, 404)


# ── Experiment publish toggle ────────────────────────────────────────────────

class TestExperimentComplete(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.other = make_user()
        self.exp = make_experiment(self.owner, complete=False)

    def test_owner_post_toggles_complete_to_true(self):
        self.client.force_login(self.owner)
        self.client.post(f'/experiments/{self.exp.pk}/complete/')
        self.exp.refresh_from_db()
        self.assertTrue(self.exp.complete)

    def test_owner_post_toggles_complete_back_to_false(self):
        self.exp.complete = True
        self.exp.save()
        self.client.force_login(self.owner)
        self.client.post(f'/experiments/{self.exp.pk}/complete/')
        self.exp.refresh_from_db()
        self.assertFalse(self.exp.complete)

    def test_non_owner_post_returns_404(self):
        self.client.force_login(self.other)
        response = self.client.post(f'/experiments/{self.exp.pk}/complete/')
        self.assertEqual(response.status_code, 404)


# ── Experiment deletion ──────────────────────────────────────────────────────

class TestExperimentDelete(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.other = make_user()
        self.exp = make_experiment(self.owner)

    def test_owner_post_deletes_experiment(self):
        self.client.force_login(self.owner)
        self.client.post(f'/experiments/{self.exp.pk}/delete/')
        self.assertFalse(Experiment.objects.filter(pk=self.exp.pk).exists())

    def test_owner_delete_redirects_to_index(self):
        self.client.force_login(self.owner)
        response = self.client.post(f'/experiments/{self.exp.pk}/delete/')
        self.assertRedirects(response, '/experiments/')

    def test_non_owner_post_returns_404(self):
        self.client.force_login(self.other)
        response = self.client.post(f'/experiments/{self.exp.pk}/delete/')
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Experiment.objects.filter(pk=self.exp.pk).exists())


# ── Task creation ────────────────────────────────────────────────────────────

class TestTaskCreate(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.exp = make_experiment(self.owner)
        self.st = make_sample_task(self.exp)
        self.client.force_login(self.owner)

    def test_create_question_task_under_experiment(self):
        before = QuestionTask.objects.count()
        self.client.post(
            f'/tasks/experiment/{self.exp.pk}/question-task/',
            {'name': 'My Q Task'},
        )
        self.assertEqual(QuestionTask.objects.count(), before + 1)

    def test_create_question_task_redirects_to_experiment(self):
        response = self.client.post(
            f'/tasks/experiment/{self.exp.pk}/question-task/',
            {'name': 'My Q Task'},
        )
        self.assertRedirects(response, f'/experiments/{self.exp.pk}/')

    def test_create_sample_task_under_experiment(self):
        before = SampleTask.objects.count()
        self.client.post(
            f'/tasks/experiment/{self.exp.pk}/sample-task/',
            {'name': 'My Sample', 'calibration': False},
        )
        self.assertEqual(SampleTask.objects.count(), before + 1)

    def test_create_click_task_under_sample_task(self):
        before = ClickTask.objects.count()
        self.client.post(
            f'/tasks/sampletask/{self.st.pk}/click-task/',
            {'name': 'Reaction', 'prompt': 'Click!', 'explanation_prompt': ''},
        )
        self.assertEqual(ClickTask.objects.count(), before + 1)

    def test_create_listening_task_under_sample_task(self):
        before = ListeningTask.objects.count()
        self.client.post(
            f'/tasks/sampletask/{self.st.pk}/listening-task/',
            {'name': 'Listen', 'listens': 2},
        )
        self.assertEqual(ListeningTask.objects.count(), before + 1)

    def test_create_intermediate_screen_under_experiment(self):
        before = IntermediateScreenTask.objects.count()
        self.client.post(
            f'/tasks/experiment/{self.exp.pk}/intermediate-screen/',
            {'name': 'Break', 'message': 'Take a breath.'},
        )
        self.assertEqual(IntermediateScreenTask.objects.count(), before + 1)


# ── Task editing ─────────────────────────────────────────────────────────────

class TestTaskEdit(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.other = make_user()
        self.exp = make_experiment(self.owner)
        self.qt = make_question_task(name='Original', sort=1, experiment=self.exp)

    def test_owner_can_get_question_task_edit_page(self):
        self.client.force_login(self.owner)
        response = self.client.get(f'/tasks/question-task/{self.qt.pk}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_owner_update_changes_name(self):
        self.client.force_login(self.owner)
        self.client.post(f'/tasks/question-task/{self.qt.pk}/update/', {'name': 'Renamed'})
        self.qt.refresh_from_db()
        self.assertEqual(self.qt.name, 'Renamed')

    def test_owner_update_redirects_to_task_edit(self):
        # After saving the task name the researcher stays on the question task
        # edit page (matching Rails redirect_back behaviour).
        self.client.force_login(self.owner)
        response = self.client.post(f'/tasks/question-task/{self.qt.pk}/update/', {'name': 'Renamed'})
        self.assertRedirects(response, f'/tasks/question-task/{self.qt.pk}/edit/')

    def test_non_owner_get_returns_404(self):
        self.client.force_login(self.other)
        response = self.client.get(f'/tasks/question-task/{self.qt.pk}/edit/')
        self.assertEqual(response.status_code, 404)


# ── Task deletion ────────────────────────────────────────────────────────────

class TestTaskDelete(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.other = make_user()
        self.exp = make_experiment(self.owner)
        self.qt = make_question_task(name='To Delete', sort=1, experiment=self.exp)

    def test_owner_post_deletes_task(self):
        self.client.force_login(self.owner)
        self.client.post(f'/tasks/question-task/{self.qt.pk}/delete/')
        self.assertFalse(QuestionTask.objects.filter(pk=self.qt.pk).exists())

    def test_owner_delete_redirects_to_experiment(self):
        self.client.force_login(self.owner)
        response = self.client.post(f'/tasks/question-task/{self.qt.pk}/delete/')
        self.assertRedirects(response, f'/experiments/{self.exp.pk}/')

    def test_non_owner_post_returns_404(self):
        self.client.force_login(self.other)
        response = self.client.post(f'/tasks/question-task/{self.qt.pk}/delete/')
        self.assertEqual(response.status_code, 404)
        self.assertTrue(QuestionTask.objects.filter(pk=self.qt.pk).exists())


# ── Question CRUD ────────────────────────────────────────────────────────────

class TestQuestionCRUD(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.other = make_user()
        self.exp = make_experiment(self.owner)
        self.qt = make_question_task(name='Q Page', sort=1, experiment=self.exp)
        self.client.force_login(self.owner)

    def test_owner_can_create_question(self):
        before = Question.objects.count()
        self.client.post(
            f'/tasks/question-task/{self.qt.pk}/questions/',
            {'question_type': 'text'},
        )
        self.assertEqual(Question.objects.count(), before + 1)

    def test_create_question_redirects_to_task_edit(self):
        response = self.client.post(
            f'/tasks/question-task/{self.qt.pk}/questions/',
            {'question_type': 'text'},
        )
        self.assertRedirects(response, f'/tasks/question-task/{self.qt.pk}/edit/')

    def test_create_rating_question_also_creates_scale(self):
        self.client.post(
            f'/tasks/question-task/{self.qt.pk}/questions/',
            {'question_type': 'rating'},
        )
        q = Question.objects.filter(question_task=self.qt, question_type='rating').first()
        self.assertIsNotNone(q)
        self.assertTrue(Scale.objects.filter(question=q).exists())

    def test_owner_can_delete_question(self):
        q = make_question(self.qt, prompt='Delete me')
        self.client.post(f'/tasks/questions/{q.pk}/delete/')
        self.assertFalse(Question.objects.filter(pk=q.pk).exists())

    def test_owner_can_update_question_prompt(self):
        q = make_question(self.qt, prompt='Old prompt')
        self.client.post(
            f'/tasks/questions/{q.pk}/update/',
            {'prompt': 'New prompt'},
        )
        q.refresh_from_db()
        self.assertEqual(q.prompt, 'New prompt')

    def test_question_type_is_immutable_after_creation(self):
        # Question type is set at creation time and cannot be changed via the
        # update endpoint (matching Rails behaviour - type is determined by which
        # "Add [type]" button the researcher clicked).
        q = make_question(self.qt, prompt='Rate this', question_type='text')
        self.client.post(
            f'/tasks/questions/{q.pk}/update/',
            {'prompt': 'Rate this', 'question_type': 'rating', 'required': False},
        )
        q.refresh_from_db()
        self.assertEqual(q.question_type, 'text')

    def test_non_owner_cannot_delete_question(self):
        q = make_question(self.qt, prompt='Protected')
        self.client.force_login(self.other)
        response = self.client.post(f'/tasks/questions/{q.pk}/delete/')
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Question.objects.filter(pk=q.pk).exists())


# ── XLSX download ────────────────────────────────────────────────────────────

class TestXLSXDownload(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.other = make_user()
        self.exp = make_experiment(self.owner, complete=True)
        make_question_task(name='Q1', sort=1, experiment=self.exp)

    def test_owner_can_download_xlsx(self):
        self.client.force_login(self.owner)
        response = self.client.get(f'/experiments/{self.exp.pk}/download/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response.get('Content-Type', ''))

    def test_download_filename_contains_experiment_name(self):
        self.client.force_login(self.owner)
        response = self.client.get(f'/experiments/{self.exp.pk}/download/')
        disposition = response.get('Content-Disposition', '')
        self.assertIn('.xlsx', disposition)

    def test_non_owner_download_returns_404(self):
        self.client.force_login(self.other)
        response = self.client.get(f'/experiments/{self.exp.pk}/download/')
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_download_redirects_to_login(self):
        response = self.client.get(f'/experiments/{self.exp.pk}/download/')
        self.assertEqual(response.status_code, 302)
        self.assertIn(LOGIN_URL, response['Location'])


# ── Admin views ──────────────────────────────────────────────────────────────

class TestAdminViews(TestCase):
    def setUp(self):
        self.admin = make_user(admin=True)
        self.researcher = make_user()

    def test_admin_can_get_users_list(self):
        self.client.force_login(self.admin)
        response = self.client.get('/accounts/admin/users/')
        self.assertEqual(response.status_code, 200)

    def test_admin_can_get_invitations_list(self):
        self.client.force_login(self.admin)
        response = self.client.get('/accounts/admin/invitations/')
        self.assertEqual(response.status_code, 200)

    def test_non_admin_redirected_from_users_list(self):
        self.client.force_login(self.researcher)
        response = self.client.get('/accounts/admin/users/')
        self.assertEqual(response.status_code, 302)

    def test_non_admin_redirected_from_invitations(self):
        self.client.force_login(self.researcher)
        response = self.client.get('/accounts/admin/invitations/')
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_users_list_redirects_to_login(self):
        response = self.client.get('/accounts/admin/users/')
        self.assertEqual(response.status_code, 302)
        self.assertIn(LOGIN_URL, response['Location'])

    def test_unauthenticated_invitations_redirects_to_login(self):
        response = self.client.get('/accounts/admin/invitations/')
        self.assertEqual(response.status_code, 302)
        self.assertIn(LOGIN_URL, response['Location'])

    def test_admin_can_create_invitation(self):
        self.client.force_login(self.admin)
        before = ResearcherInvitation.objects.count()
        self.client.post('/accounts/admin/invitations/new/')
        self.assertEqual(ResearcherInvitation.objects.count(), before + 1)

    def test_admin_users_list_shows_all_users(self):
        self.client.force_login(self.admin)
        response = self.client.get('/accounts/admin/users/')
        users = list(response.context['users'])
        pks = [u.pk for u in users]
        self.assertIn(self.admin.pk, pks)
        self.assertIn(self.researcher.pk, pks)
