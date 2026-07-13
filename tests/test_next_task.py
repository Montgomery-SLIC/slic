"""
Tests for responses.helpers.next_task - the participant sequencing logic.

Covers: linear ordering, visited/unvisited distinction, random group selection,
        SampleTask intro URL, recursion from subtasks back to experiment.
"""
from django.test import TestCase
from django.urls import reverse

from responses.helpers import next_task
from responses.models import Visit

from .factories import make_user, make_experiment, make_question_task, make_sample_task, make_click_task


class TestNextTaskLinear(TestCase):
    def setUp(self):
        user = make_user()
        self.exp = make_experiment(user, complete=True)
        self.slug = self.exp.slug
        self.pid = 99
        self.t1 = make_question_task(name='Q1', sort=1, experiment=self.exp)
        self.t2 = make_question_task(name='Q2', sort=2, experiment=self.exp)
        self.t3 = make_question_task(name='Q3', sort=3, experiment=self.exp)

    def _visit(self, task, visited=True):
        Visit.objects.create(participant_id=self.pid, task_id=task.pk, visited=visited)

    def _task_url(self, task):
        return reverse('responses:task_view', kwargs={
            'slug': self.slug,
            'participant_id': self.pid,
            'task_type': 'questiontask',
            'task_id': task.pk,
        })

    def test_returns_first_task_when_no_visits_exist(self):
        self.assertEqual(next_task(self.exp, self.pid, self.slug), self._task_url(self.t1))

    def test_skips_visited_task_in_sort_order(self):
        self._visit(self.t1)
        self.assertEqual(next_task(self.exp, self.pid, self.slug), self._task_url(self.t2))

    def test_unvisited_visit_row_does_not_count(self):
        # A Visit row with visited=False still leaves the task as "next"
        self._visit(self.t1, visited=False)
        self.assertEqual(next_task(self.exp, self.pid, self.slug), self._task_url(self.t1))

    def test_returns_finish_url_when_all_tasks_visited(self):
        for t in [self.t1, self.t2, self.t3]:
            self._visit(t)
        expected = reverse('responses:finish', kwargs={
            'slug': self.slug, 'participant_id': self.pid,
        })
        self.assertEqual(next_task(self.exp, self.pid, self.slug), expected)

    def test_visits_from_other_participant_ignored(self):
        other_pid = 9999
        Visit.objects.create(participant_id=other_pid, task_id=self.t1.pk, visited=True)
        # Our participant has no visits - should still get t1
        self.assertEqual(next_task(self.exp, self.pid, self.slug), self._task_url(self.t1))


class TestNextTaskSampleTask(TestCase):
    def setUp(self):
        user = make_user()
        self.exp = make_experiment(user, complete=True)
        self.slug = self.exp.slug
        self.pid = 42
        self.sample = make_sample_task(self.exp, name='Sample', sort=1)
        self.ct1 = make_click_task(self.sample, name='Click1', sort=1)
        self.ct2 = make_click_task(self.sample, name='Click2', sort=2)

    def _visit(self, task, visited=True):
        Visit.objects.create(participant_id=self.pid, task_id=task.pk, visited=visited)

    def test_returns_sample_intro_for_unvisited_sample_task(self):
        # Sample task has a Visit row but not yet visited
        self._visit(self.sample, visited=False)
        expected = reverse('responses:sample_intro', kwargs={
            'slug': self.slug,
            'participant_id': self.pid,
            'sample_id': self.sample.pk,
        })
        self.assertEqual(next_task(self.exp, self.pid, self.slug), expected)

    def test_recurses_to_experiment_when_all_subtasks_visited(self):
        # Experiment level: sample is visited
        self._visit(self.sample)
        # Subtask level: both click tasks visited
        self._visit(self.ct1)
        self._visit(self.ct2)

        # Starting from within the sample - should recurse up then hit finish
        expected = reverse('responses:finish', kwargs={
            'slug': self.slug, 'participant_id': self.pid,
        })
        self.assertEqual(next_task(self.sample, self.pid, self.slug), expected)

    def test_returns_next_subtask_within_sample(self):
        self._visit(self.ct1)
        # ct2 is still unvisited
        expected = reverse('responses:task_view', kwargs={
            'slug': self.slug,
            'participant_id': self.pid,
            'task_type': 'clicktask',
            'task_id': self.ct2.pk,
        })
        self.assertEqual(next_task(self.sample, self.pid, self.slug), expected)


class TestNextTaskRandomGroup(TestCase):
    def setUp(self):
        user = make_user()
        self.exp = make_experiment(user, complete=True)
        self.slug = self.exp.slug
        self.pid = 7

    def test_random_tasks_produce_variety(self):
        t1 = make_question_task(name='R1', sort=1, experiment=self.exp)
        t2 = make_question_task(name='R2', sort=2, experiment=self.exp)
        t3 = make_question_task(name='R3', sort=3, experiment=self.exp)
        for t in [t1, t2, t3]:
            t.random = True
            t.save(update_fields=['random'])

        valid_urls = {
            reverse('responses:task_view', kwargs={
                'slug': self.slug, 'participant_id': self.pid,
                'task_type': 'questiontask', 'task_id': t.pk,
            })
            for t in [t1, t2, t3]
        }

        chosen = {next_task(self.exp, self.pid, self.slug) for _ in range(30)}
        # All chosen URLs must be from the valid set
        self.assertTrue(chosen.issubset(valid_urls))
        # With 30 draws across 3 options, we expect at least 2 distinct URLs
        self.assertGreaterEqual(len(chosen), 2)

    def test_non_random_task_returned_first_before_random_group(self):
        non_random = make_question_task(name='First', sort=1, experiment=self.exp)
        random_t = make_question_task(name='Rand', sort=2, experiment=self.exp)
        random_t.random = True
        random_t.save(update_fields=['random'])

        url = next_task(self.exp, self.pid, self.slug)
        expected = reverse('responses:task_view', kwargs={
            'slug': self.slug, 'participant_id': self.pid,
            'task_type': 'questiontask', 'task_id': non_random.pk,
        })
        self.assertEqual(url, expected)
