from experiments.models import Experiment
from tests.e2e.conftest import login


def test_unauthenticated_redirects_to_login(page, live_server):
    page.goto(f"{live_server.url}/experiments/")
    assert "login" in page.url


def test_authenticated_user_reaches_experiments(page, live_server, researcher):
    login(page, live_server, researcher)
    page.goto(f"{live_server.url}/experiments/")
    assert "/experiments/" in page.url


def test_login_form_rejects_wrong_password(page, live_server, researcher):
    page.goto(f"{live_server.url}/accounts/login/")
    page.fill("input[name='login']", "researcher@example.com")
    page.fill("input[name='password']", "wrongpassword")
    page.click("button[type='submit']")
    assert "login" in page.url


def test_create_experiment(page, live_server, researcher):
    login(page, live_server, researcher)
    page.goto(f"{live_server.url}/experiments/new/")
    page.fill("input[name='name']", "My New Experiment")
    page.click("button[type='submit']")
    assert "My New Experiment" in page.content()


def test_edit_experiment_name(page, live_server, researcher, db):
    exp = Experiment(user=researcher, name="Original Name", complete=False)
    exp.save()
    login(page, live_server, researcher)
    page.goto(f"{live_server.url}/experiments/{exp.pk}/edit/")
    page.fill("input[name='name']", "Updated Name")
    page.click("button[type='submit']")
    assert "Updated Name" in page.content()


def test_publish_experiment_blocked_without_tasks(page, live_server, researcher, db):
    exp = Experiment(user=researcher, name="Unpublished Study", complete=False)
    exp.save()
    login(page, live_server, researcher)
    page.goto(f"{live_server.url}/experiments/{exp.pk}/")
    page.locator(f"form[action='/experiments/{exp.pk}/complete/'] button").click()
    exp.refresh_from_db()
    assert exp.complete is False  # blocked by completion validation - no tasks


def test_add_question_task(page, live_server, researcher, db):
    exp = Experiment(user=researcher, name="Study", complete=False)
    exp.save()
    login(page, live_server, researcher)
    page.goto(f"{live_server.url}/tasks/experiment/{exp.pk}/question-task/new/")
    page.fill("input[name='name']", "My Question Page")
    page.click("button[type='submit']")
    assert "My Question Page" in page.content()


def test_download_xlsx(page, live_server, published_experiment, researcher):
    login(page, live_server, researcher)
    page.goto(f"{live_server.url}/experiments/{published_experiment.pk}/")
    with page.expect_download() as download_info:
        page.locator("a[href*='download']").click()
    assert ".xlsx" in download_info.value.suggested_filename
