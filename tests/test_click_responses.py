"""
Tests for the click response XHR endpoint (POST /click-responses/).

Covers: timestamp accuracy, auth enforcement via Visit existence check,
        multiple clicks, malformed input rejection.
"""
import json
from django.test import TestCase

from responses.models import ClickResponse, Visit

from .factories import make_user, make_experiment, make_sample_task, make_click_task

ENDPOINT = '/click-responses/'


class TestClickResponseView(TestCase):
    def setUp(self):
        user = make_user()
        self.exp = make_experiment(user, complete=True)
        self.sample = make_sample_task(self.exp)
        self.ct = make_click_task(self.sample)
        self.pid = 5
        Visit.objects.create(participant_id=self.pid, task_id=self.ct.pk, visited=False)

    def _post(self, payload):
        return self.client.post(
            ENDPOINT,
            json.dumps(payload),
            content_type='application/json',
        )

    def _minimal_item(self, **overrides):
        base = {
            'click_task_id': self.ct.pk,
            'participant_id': self.pid,
            'time': 1.0,
            'answer': '',
        }
        base.update(overrides)
        return base

    # ── Happy path ──────────────────────────────────────────────────────────

    def test_valid_click_returns_ok(self):
        response = self._post([self._minimal_item()])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'ok': True})

    def test_click_response_stored_in_db(self):
        self._post([self._minimal_item(time=2.718, answer='test')])
        cr = ClickResponse.objects.get(participant_id=self.pid, click_task=self.ct)
        self.assertAlmostEqual(cr.time, 2.718, places=10)
        self.assertEqual(cr.answer, 'test')

    def test_time_zero_stored_correctly(self):
        self._post([self._minimal_item(time=0.0)])
        cr = ClickResponse.objects.get(participant_id=self.pid, click_task=self.ct)
        self.assertEqual(cr.time, 0.0)

    def test_time_none_stored_as_null(self):
        self._post([self._minimal_item(time=None)])
        cr = ClickResponse.objects.get(participant_id=self.pid, click_task=self.ct)
        self.assertIsNone(cr.time)

    def test_multiple_clicks_all_stored(self):
        ct2 = make_click_task(self.sample, name='Click2', sort=2)
        Visit.objects.create(participant_id=self.pid, task_id=ct2.pk, visited=False)

        self._post([
            self._minimal_item(time=1.1, answer='first'),
            {'click_task_id': ct2.pk, 'participant_id': self.pid, 'time': 2.2, 'answer': 'second'},
        ])
        self.assertEqual(ClickResponse.objects.filter(participant_id=self.pid).count(), 2)

    def test_no_clicks_explanation_flag_stored(self):
        self._post([self._minimal_item(no_clicks_explanation=True)])
        cr = ClickResponse.objects.get(participant_id=self.pid, click_task=self.ct)
        self.assertTrue(cr.no_clicks_explanation)

    def test_from_checkbox_flag_stored(self):
        self._post([self._minimal_item(from_checkbox=True)])
        cr = ClickResponse.objects.get(participant_id=self.pid, click_task=self.ct)
        self.assertTrue(cr.from_checkbox)

    # ── Timestamp precision ──────────────────────────────────────────────────

    def test_float_timestamp_precision_preserved(self):
        """PostgreSQL DOUBLE PRECISION must preserve float precision to ~15 digits."""
        t = 123.456789012345
        self._post([self._minimal_item(time=t)])
        cr = ClickResponse.objects.get(participant_id=self.pid, click_task=self.ct)
        self.assertAlmostEqual(cr.time, t, places=9)

    # ── Auth enforcement ─────────────────────────────────────────────────────

    def test_no_visit_returns_403(self):
        pid_without_visit = 9999
        response = self._post([{
            'click_task_id': self.ct.pk,
            'participant_id': pid_without_visit,
            'time': 1.0,
            'answer': '',
        }])
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'unauthorized')
        self.assertEqual(ClickResponse.objects.count(), 0)

    # ── Malformed input ──────────────────────────────────────────────────────

    def test_invalid_json_returns_400(self):
        response = self.client.post(ENDPOINT, 'not valid json', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_payload_not_a_list_returns_400(self):
        response = self._post({'click_task_id': self.ct.pk, 'participant_id': self.pid})
        self.assertEqual(response.status_code, 400)

    def test_missing_click_task_id_returns_400(self):
        response = self._post([{'participant_id': self.pid, 'time': 1.0}])
        self.assertEqual(response.status_code, 400)

    def test_missing_participant_id_returns_400(self):
        response = self._post([{'click_task_id': self.ct.pk, 'time': 1.0}])
        self.assertEqual(response.status_code, 400)

    def test_empty_list_returns_ok(self):
        response = self._post([])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'ok': True})
