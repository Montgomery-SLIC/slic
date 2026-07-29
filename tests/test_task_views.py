"""
Tests for task-level views: randomise toggle and audio upload.
"""
import io
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from tasks.models import SampleTask, QuestionTask
from .factories import make_user, make_experiment, make_question_task, make_sample_task

LOGIN_URL = '/accounts/login/'


# ── task_random ──────────────────────────────────────────────────────────────

class TestTaskRandom(TestCase):
    def setUp(self):
        self.user = make_user()
        self.exp = make_experiment(self.user)
        self.task = make_question_task(experiment=self.exp, sort=1)

    def test_post_redirects_to_experiment_page(self):
        self.client.force_login(self.user)
        response = self.client.post(f'/tasks/task/{self.task.pk}/random/')
        self.assertRedirects(response, f'/experiments/{self.exp.pk}/', fetch_redirect_response=False)

    def test_post_toggles_random_on(self):
        self.client.force_login(self.user)
        self.assertFalse(self.task.random)
        self.client.post(f'/tasks/task/{self.task.pk}/random/')
        self.task.refresh_from_db()
        self.assertTrue(self.task.random)

    def test_post_toggles_random_off(self):
        self.task.random = True
        self.task.save(update_fields=['random'])
        self.client.force_login(self.user)
        self.client.post(f'/tasks/task/{self.task.pk}/random/')
        self.task.refresh_from_db()
        self.assertFalse(self.task.random)

    def test_get_returns_json(self):
        self.client.force_login(self.user)
        response = self.client.get(f'/tasks/task/{self.task.pk}/random/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_unauthenticated_post_redirects_to_login(self):
        response = self.client.post(f'/tasks/task/{self.task.pk}/random/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_other_user_gets_404(self):
        other = make_user()
        self.client.force_login(other)
        response = self.client.post(f'/tasks/task/{self.task.pk}/random/')
        self.assertEqual(response.status_code, 404)

    def test_sample_task_nested_redirects_to_parent_experiment(self):
        sample = make_sample_task(self.exp, sort=2)
        qt = make_question_task(name='Sub Q', sort=1, sample_task=sample)
        self.client.force_login(self.user)
        response = self.client.post(f'/tasks/task/{qt.pk}/random/')
        self.assertRedirects(response, f'/experiments/{self.exp.pk}/', fetch_redirect_response=False)


# ── audio_upload ─────────────────────────────────────────────────────────────

def _wav_file(name='test.wav', size=1024):
    """Return a minimal in-memory WAV file for upload testing."""
    return SimpleUploadedFile(name, b'\x00' * size, content_type='audio/wav')


@override_settings(MEDIA_ROOT='/tmp/slic_test_media')
class TestAudioUpload(TestCase):
    def setUp(self):
        self.user = make_user()
        self.exp = make_experiment(self.user)
        self.sample = make_sample_task(self.exp, sort=1)

    def test_valid_upload_shows_success_message(self):
        self.client.force_login(self.user)
        response = self.client.post(
            f'/tasks/sample-task/{self.sample.pk}/audio/',
            {'audio': _wav_file()},
            follow=True,
        )
        messages = [str(m) for m in response.context['messages']]
        self.assertTrue(any('uploaded' in m.lower() for m in messages))

    def test_valid_upload_redirects_to_edit_page(self):
        self.client.force_login(self.user)
        response = self.client.post(
            f'/tasks/sample-task/{self.sample.pk}/audio/',
            {'audio': _wav_file()},
        )
        self.assertRedirects(
            response, f'/tasks/sample-task/{self.sample.pk}/edit/', fetch_redirect_response=False,
        )

    def test_non_wav_file_is_accepted(self):
        self.client.force_login(self.user)
        mp3_file = SimpleUploadedFile('test.mp3', b'\x00' * 512, content_type='audio/mpeg')
        response = self.client.post(
            f'/tasks/sample-task/{self.sample.pk}/audio/',
            {'audio': mp3_file},
            follow=True,
        )
        messages = [str(m) for m in response.context['messages']]
        self.assertTrue(any('uploaded' in m.lower() for m in messages))

    def test_oversized_file_rejected_by_form(self):
        from tasks.forms import AudioUploadForm
        big_file = SimpleUploadedFile('big.wav', b'\x00' * 10, content_type='audio/wav')
        big_file.size = 314572800  # at the 300 MB boundary
        form = AudioUploadForm(data={}, files={'audio': big_file})
        self.assertFalse(form.is_valid())
        self.assertIn('300', str(form.errors))

    def test_unauthenticated_redirects_to_login(self):
        response = self.client.post(
            f'/tasks/sample-task/{self.sample.pk}/audio/',
            {'audio': _wav_file()},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_other_user_gets_404(self):
        other = make_user()
        self.client.force_login(other)
        response = self.client.post(
            f'/tasks/sample-task/{self.sample.pk}/audio/',
            {'audio': _wav_file()},
        )
        self.assertEqual(response.status_code, 404)
