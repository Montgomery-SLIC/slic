"""
Tests for participant_id assignment correctness and atomicity.

The sequential tests verify that IDs increment correctly (1, 2, 3…).
The concurrent test verifies that the select_for_update() row lock
prevents duplicate participant_ids under real simultaneous starts.
"""
import threading

from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, RequestFactory, Client

from responses.models import ParticipantId, Visit
from responses.views import ExperimentStartView

from .factories import make_user, make_experiment, make_question_task


class TestParticipantIdSequential(TestCase):
    """Sequential correctness: each start gets the next available ID."""

    def setUp(self):
        user = make_user()
        self.exp = make_experiment(user, complete=True)
        make_question_task(name='Q1', sort=1, experiment=self.exp)

    def _start(self):
        return Client().post(
            f'/{self.exp.slug}/start/',
            {'consent': 'on', 'email': ''},
        )

    def test_first_start_gets_participant_id_1(self):
        self._start()
        pid = ParticipantId.objects.get(experiment=self.exp)
        self.assertEqual(pid.participant_id, 1)

    def test_second_start_gets_participant_id_2(self):
        self._start()
        self._start()
        pids = sorted(
            ParticipantId.objects
            .filter(experiment=self.exp)
            .values_list('participant_id', flat=True)
        )
        self.assertEqual(pids, [1, 2])

    def test_participant_ids_are_unique_per_experiment(self):
        user2 = make_user()
        exp2 = make_experiment(user2, complete=True)
        make_question_task(name='Q1', sort=1, experiment=exp2)

        self._start()  # exp → pid 1

        Client().post(f'/{exp2.slug}/start/', {'consent': 'on', 'email': ''})  # exp2 → pid 1

        # Both experiments independently start from 1
        for exp in [self.exp, exp2]:
            pids = list(
                ParticipantId.objects
                .filter(experiment=exp)
                .values_list('participant_id', flat=True)
            )
            self.assertEqual(pids, [1])

    def test_visit_rows_created_for_each_participant(self):
        self._start()
        self._start()
        # Each participant has their own set of Visit rows
        for pid in [1, 2]:
            qt_pk = self.exp.tasks.first().pk
            self.assertTrue(Visit.objects.filter(participant_id=pid, task_id=qt_pk).exists())


class TestParticipantIdConcurrent(TransactionTestCase):
    """
    Concurrent correctness: two simultaneous starts must produce distinct IDs.

    Uses TransactionTestCase (no wrapping transaction) so each thread opens
    its own real PostgreSQL connection, making select_for_update() meaningful.
    """

    def setUp(self):
        user = make_user()
        self.exp = make_experiment(user, complete=True)
        make_question_task(name='Q1', sort=1, experiment=self.exp)

    def test_concurrent_starts_produce_distinct_participant_ids(self):
        results = []
        errors = []
        barrier = threading.Barrier(2)  # both threads start the view call together

        def run_start():
            close_old_connections()
            try:
                factory = RequestFactory()
                request = factory.post(
                    f'/{self.exp.slug}/start/',
                    {'consent': 'on', 'email': ''},
                )
                barrier.wait()  # synchronise thread entry into the view
                resp = ExperimentStartView.as_view()(request, slug=self.exp.slug)
                results.append(resp.status_code)
            except Exception as exc:
                errors.append(str(exc))
            finally:
                close_old_connections()

        threads = [threading.Thread(target=run_start) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        self.assertEqual(errors, [], f'Thread errors: {errors}')
        self.assertEqual(len(results), 2, 'Both threads must complete')

        pids = sorted(
            ParticipantId.objects
            .filter(experiment=self.exp)
            .values_list('participant_id', flat=True)
        )
        self.assertEqual(len(pids), 2, f'Expected 2 participants, got: {pids}')
        # IDs must be distinct - no duplicates
        self.assertEqual(len(set(pids)), 2, f'Duplicate participant_ids: {pids}')
