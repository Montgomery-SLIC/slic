"""Tests for the completion_errors() validation system."""
from django.test import TestCase

from experiments.models import Experiment
from tasks.models import (
    QuestionTask, SampleTask, ClickTask,
    Question, Option, Scale,
    QUESTION_TYPE_TEXT, QUESTION_TYPE_CHECKBOX, QUESTION_TYPE_RADIO,
    QUESTION_TYPE_DROPDOWN, QUESTION_TYPE_RATING, QUESTION_DEFAULT_PROMPTS,
)
from tests.factories import make_user, make_experiment, make_question_task, make_sample_task, make_question


# ── Question.completion_errors ──────────────────────────────────────────────

class TestQuestionCompletionErrors(TestCase):
    def setUp(self):
        self.user = make_user()
        self.exp = make_experiment(self.user)
        self.qt = make_question_task('page 1', 1, experiment=self.exp)

    def test_default_prompt_text_is_a_warning(self):
        q = Question.objects.create(
            question_task=self.qt, question_type=QUESTION_TYPE_TEXT,
            prompt=QUESTION_DEFAULT_PROMPTS[QUESTION_TYPE_TEXT], sort=1,
        )
        result = q.completion_errors()
        self.assertEqual(len(result['warnings']), 1)
        self.assertIn('still has default prompt', result['warnings'][0])
        self.assertEqual(result['errors'], [])

    def test_custom_prompt_no_warning(self):
        q = Question.objects.create(
            question_task=self.qt, question_type=QUESTION_TYPE_TEXT,
            prompt='My own question', sort=1,
        )
        result = q.completion_errors()
        self.assertEqual(result['warnings'], [])
        self.assertEqual(result['errors'], [])

    def test_checkbox_no_options_is_error(self):
        q = Question.objects.create(
            question_task=self.qt, question_type=QUESTION_TYPE_CHECKBOX,
            prompt='Pick one', sort=1,
        )
        errors = q.completion_errors()['errors']
        self.assertTrue(any('no options' in e for e in errors))

    def test_checkbox_with_options_no_error(self):
        q = Question.objects.create(
            question_task=self.qt, question_type=QUESTION_TYPE_CHECKBOX,
            prompt='Pick one', sort=1,
        )
        Option.objects.create(question=q, contents='Option A')
        self.assertEqual(q.completion_errors()['errors'], [])

    def test_radio_no_options_is_error(self):
        q = Question.objects.create(
            question_task=self.qt, question_type=QUESTION_TYPE_RADIO,
            prompt='Choose', sort=1,
        )
        self.assertTrue(any('no options' in e for e in q.completion_errors()['errors']))

    def test_dropdown_no_options_is_error(self):
        q = Question.objects.create(
            question_task=self.qt, question_type=QUESTION_TYPE_DROPDOWN,
            prompt='Choose', sort=1,
        )
        self.assertTrue(any('no options' in e for e in q.completion_errors()['errors']))

    def test_rating_no_scale_is_error(self):
        q = Question.objects.create(
            question_task=self.qt, question_type=QUESTION_TYPE_RATING,
            prompt='Rate it', sort=1,
        )
        self.assertTrue(any('no scale' in e for e in q.completion_errors()['errors']))

    def test_rating_with_scale_no_error(self):
        q = Question.objects.create(
            question_task=self.qt, question_type=QUESTION_TYPE_RATING,
            prompt='Rate it', sort=1,
        )
        Scale.objects.create(question=q, bins=7, low='Bad', high='Good')
        self.assertEqual(q.completion_errors()['errors'], [])

    def test_default_prompt_fires_warning_for_all_types(self):
        for qtype, default in QUESTION_DEFAULT_PROMPTS.items():
            with self.subTest(qtype=qtype):
                q = Question.objects.create(
                    question_task=self.qt, question_type=qtype, prompt=default, sort=99,
                )
                warns = q.completion_errors()['warnings']
                self.assertEqual(len(warns), 1)
                q.delete()


# ── QuestionTask.completion_errors ──────────────────────────────────────────

class TestQuestionTaskCompletionErrors(TestCase):
    def setUp(self):
        self.user = make_user()
        self.exp = make_experiment(self.user)

    def test_empty_question_page_is_error(self):
        qt = make_question_task('q page', 1, experiment=self.exp)
        errors = qt.completion_errors()['errors']
        self.assertTrue(any('does not contain any questions' in e for e in errors))

    def test_question_with_default_prompt_is_warning_not_error(self):
        qt = make_question_task('q page', 1, experiment=self.exp)
        Question.objects.create(
            question_task=qt, question_type=QUESTION_TYPE_TEXT,
            prompt=QUESTION_DEFAULT_PROMPTS[QUESTION_TYPE_TEXT], sort=1,
        )
        result = qt.completion_errors()
        self.assertEqual(result['errors'], [])
        self.assertEqual(len(result['warnings']), 1)


# ── SampleTask.completion_errors ────────────────────────────────────────────

class TestSampleTaskCompletionErrors(TestCase):
    def setUp(self):
        self.user = make_user()
        self.exp = make_experiment(self.user)

    def test_no_audio_is_error(self):
        st = make_sample_task(self.exp)
        errors = st.completion_errors()['errors']
        self.assertTrue(any('no audio file' in e for e in errors))

    def test_with_audio_set_no_error(self):
        st = make_sample_task(self.exp)
        st.audio.name = 'audio/fake.wav'
        errors = st.completion_errors()['errors']
        self.assertEqual(errors, [])

    def test_calibration_without_click_task_is_warning(self):
        st = SampleTask.objects.create(
            name='cal', experiment=self.exp, sort=1, calibration=True,
        )
        st.audio.name = 'audio/fake.wav'
        warns = st.completion_errors()['warnings']
        self.assertTrue(any('calibration' in w for w in warns))

    def test_click_task_no_transcript_is_error(self):
        st = make_sample_task(self.exp)
        st.audio.name = 'audio/fake.wav'
        ClickTask.objects.create(name='click', sample_task=st, sort=1)
        errors = st.completion_errors()['errors']
        self.assertTrue(any('no transcript' in e for e in errors))

    def test_click_task_with_transcript_no_error(self):
        st = make_sample_task(self.exp)
        st.audio.name = 'audio/fake.wav'
        st.transcript.name = 'transcripts/fake.eaf'
        ClickTask.objects.create(name='click', sample_task=st, sort=1)
        errors = st.completion_errors()['errors']
        self.assertEqual(errors, [])

    def test_calibration_with_click_task_no_transcript_error_suppressed(self):
        # Calibration samples skip the transcript requirement
        st = SampleTask.objects.create(
            name='cal', experiment=self.exp, sort=1, calibration=True,
        )
        st.audio.name = 'audio/fake.wav'
        ClickTask.objects.create(name='click', sample_task=st, sort=1)
        result = st.completion_errors()
        self.assertFalse(any('no transcript' in e for e in result['errors']))
        self.assertEqual(result['warnings'], [])


# ── Experiment.completion_errors ────────────────────────────────────────────

class TestExperimentCompletionErrors(TestCase):
    def setUp(self):
        self.user = make_user()
        self.exp = make_experiment(self.user)

    def test_no_tasks_is_error(self):
        errors = self.exp.completion_errors()['errors']
        self.assertTrue(any('does not contain any tasks' in e for e in errors))

    def test_aggregates_task_errors(self):
        make_sample_task(self.exp)  # no audio
        errors = self.exp.completion_errors()['errors']
        self.assertTrue(any('no audio file' in e for e in errors))

    def test_aggregates_task_warnings(self):
        qt = make_question_task('q page', 1, experiment=self.exp)
        Question.objects.create(
            question_task=qt, question_type=QUESTION_TYPE_TEXT,
            prompt=QUESTION_DEFAULT_PROMPTS[QUESTION_TYPE_TEXT], sort=1,
        )
        result = self.exp.completion_errors()
        self.assertEqual(result['errors'], [])
        self.assertEqual(len(result['warnings']), 1)

    def test_clean_experiment_no_errors(self):
        qt = make_question_task('q page', 1, experiment=self.exp)
        Question.objects.create(
            question_task=qt, question_type=QUESTION_TYPE_TEXT,
            prompt='My question', sort=1,
        )
        result = self.exp.completion_errors()
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['warnings'], [])


# ── ExperimentCompleteView publish flow ─────────────────────────────────────

class TestExperimentCompleteView(TestCase):
    def setUp(self):
        self.user = make_user()
        self.exp = make_experiment(self.user)
        self.client.force_login(self.user)
        self.url = f'/experiments/{self.exp.pk}/complete/'

    def test_publish_blocked_by_errors(self):
        # experiment has no tasks → error
        self.client.post(self.url)
        self.exp.refresh_from_db()
        self.assertFalse(self.exp.complete)

    def test_publish_succeeds_when_clean(self):
        qt = make_question_task('q page', 1, experiment=self.exp)
        Question.objects.create(
            question_task=qt, question_type=QUESTION_TYPE_TEXT,
            prompt='My question', sort=1,
        )
        self.client.post(self.url)
        self.exp.refresh_from_db()
        self.assertTrue(self.exp.complete)

    def test_publish_with_warnings_requires_force(self):
        qt = make_question_task('q page', 1, experiment=self.exp)
        Question.objects.create(
            question_task=qt, question_type=QUESTION_TYPE_TEXT,
            prompt=QUESTION_DEFAULT_PROMPTS[QUESTION_TYPE_TEXT], sort=1,
        )
        self.client.post(self.url)
        self.exp.refresh_from_db()
        self.assertFalse(self.exp.complete)

    def test_publish_with_force_publishes_despite_warnings(self):
        qt = make_question_task('q page', 1, experiment=self.exp)
        Question.objects.create(
            question_task=qt, question_type=QUESTION_TYPE_TEXT,
            prompt=QUESTION_DEFAULT_PROMPTS[QUESTION_TYPE_TEXT], sort=1,
        )
        self.client.post(self.url, data={'force': '1'})
        self.exp.refresh_from_db()
        self.assertTrue(self.exp.complete)

    def test_unpublish_always_succeeds(self):
        self.exp.complete = True
        self.exp.save()
        self.client.post(self.url)
        self.exp.refresh_from_db()
        self.assertFalse(self.exp.complete)
