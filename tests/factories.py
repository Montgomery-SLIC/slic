"""
Lightweight model factories for tests - no factory_boy required.
"""
from django.contrib.auth import get_user_model

from experiments.models import Experiment
from tasks.models import (
    QuestionTask, SampleTask, ClickTask,
    ListeningTask, IntermediateScreenTask, Question,
)

User = get_user_model()

_counter = 0


def _uid():
    global _counter
    _counter += 1
    return _counter


def make_user(email=None, password='testpass123', admin=False):
    if email is None:
        email = f'user{_uid()}@example.com'
    user = User()
    user.email = email
    user.is_active = True
    user.admin = admin
    user.is_staff = admin
    user.is_superuser = admin
    user.set_password(password)
    user.save()
    return user


def make_experiment(user, name='Test Experiment', complete=False):
    exp = Experiment(user=user, name=name, complete=complete)
    exp.save()
    return exp


def _base_kwargs(name, sort, experiment, sample_task):
    kw = {'name': name, 'sort': sort}
    if experiment is not None:
        kw['experiment'] = experiment
    elif sample_task is not None:
        kw['sample_task'] = sample_task
    return kw


def make_question_task(name='Q Page', sort=1, experiment=None, sample_task=None):
    qt = QuestionTask(**_base_kwargs(name, sort, experiment, sample_task))
    qt.save()
    return qt


def make_sample_task(experiment, name='Sample', sort=1):
    st = SampleTask(name=name, sort=sort, experiment=experiment)
    st.save()
    return st


def make_click_task(sample_task, name='Click', sort=1, prompt='Click when you hear it'):
    ct = ClickTask(name=name, sort=sort, sample_task=sample_task, prompt=prompt)
    ct.save()
    return ct


def make_listening_task(sample_task, name='Listen', sort=1, listens=1):
    lt = ListeningTask(name=name, sort=sort, sample_task=sample_task, listens=listens)
    lt.save()
    return lt


def make_question(question_task, prompt='How do you feel?', sort=1,
                  required=False, question_type='text'):
    q = Question(
        question_task=question_task,
        prompt=prompt,
        sort=sort,
        required=required,
        question_type=question_type,
    )
    q.save()
    return q
