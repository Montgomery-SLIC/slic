from experiments.models import Experiment
from responses.models import ParticipantId


def test_home_loads_for_published_experiment(page, live_server, published_experiment):
    page.goto(f"{live_server.url}/{published_experiment.slug}/home/")
    assert published_experiment.name in page.content()


def test_home_404_for_unpublished_experiment(page, live_server, researcher, db):
    exp = Experiment(user=researcher, name="Draft", complete=False)
    exp.save()
    response = page.goto(f"{live_server.url}/{exp.slug}/home/")
    assert response.status == 404


def test_start_without_consent_stays_on_home(page, live_server, published_experiment):
    page.goto(f"{live_server.url}/{published_experiment.slug}/home/")
    # HTML5 required on the consent checkbox blocks submission without checking it
    page.click("button[type='submit']")
    assert published_experiment.slug in page.url


def test_start_with_consent_redirects_to_task(page, live_server, published_experiment):
    page.goto(f"{live_server.url}/{published_experiment.slug}/home/")
    page.fill("input[name='email']", "participant@example.com")
    page.check("input[name='consent']")
    page.click("button[type='submit']")
    assert "questiontask" in page.url


def test_task_page_shows_task_name(page, live_server, published_experiment):
    page.goto(f"{live_server.url}/{published_experiment.slug}/home/")
    page.fill("input[name='email']", "participant@example.com")
    page.check("input[name='consent']")
    page.click("button[type='submit']")
    assert "Q1" in page.content()


def test_submitting_task_reaches_finish(page, live_server, published_experiment):
    page.goto(f"{live_server.url}/{published_experiment.slug}/home/")
    page.fill("input[name='email']", "participant@example.com")
    page.check("input[name='consent']")
    page.click("button[type='submit']")
    # Q1 has no questions so submitting goes straight to finish
    page.click("button[type='submit']")
    assert "finish" in page.url


def test_finish_page_loads(page, live_server, published_experiment, db):
    pid_rec = ParticipantId(experiment=published_experiment, participant_id=99)
    pid_rec.email = ""
    pid_rec.save()
    page.goto(f"{live_server.url}/{published_experiment.slug}/99/finish/")
    assert page.locator("h1, h2").first.is_visible()
