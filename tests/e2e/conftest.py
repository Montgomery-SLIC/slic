import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import pytest
from django.contrib.auth import get_user_model
from django.test import Client as DjangoClient
from experiments.models import Experiment
from tasks.models import QuestionTask


@pytest.fixture
def researcher(db):
    User = get_user_model()
    user = User()
    user.email = "researcher@example.com"
    user.is_active = True
    user.set_password("testpass123")
    user.save()
    return user


@pytest.fixture
def published_experiment(db, researcher):
    exp = Experiment(user=researcher, name="Test Study", complete=True)
    exp.save()
    qt = QuestionTask(name="Q1", sort=1, experiment=exp)
    qt.save()
    return exp


def login(page, live_server, user):
    """Inject a Django session cookie so Playwright is logged in as the given user.

    Uses force_login to bypass the allauth form - necessary because the encrypted
    email blind index cannot be looked up without a real BLIND_INDEX_KEY in dev.
    """
    client = DjangoClient()
    client.force_login(user)
    page.context.add_cookies([{
        'name': 'sessionid',
        'value': client.cookies['sessionid'].value,
        'url': live_server.url,
    }])