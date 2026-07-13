from django.contrib.auth import get_user_model
from tests.e2e.conftest import login


def test_navbar_shows_signin_when_logged_out(page, live_server):
    page.goto(f"{live_server.url}/")
    assert page.locator("a", has_text="Sign in").is_visible()


def test_navbar_hides_experiments_when_logged_out(page, live_server):
    page.goto(f"{live_server.url}/")
    assert not page.locator("a", has_text="Experiments").is_visible()


def test_navbar_shows_experiments_when_logged_in(page, live_server, researcher):
    login(page, live_server, researcher)
    page.goto(f"{live_server.url}/")
    assert page.locator("a", has_text="Experiments").is_visible()


def test_navbar_hides_signin_when_logged_in(page, live_server, researcher):
    login(page, live_server, researcher)
    page.goto(f"{live_server.url}/")
    assert not page.locator("a", has_text="Sign in").is_visible()


def test_signout_returns_to_logged_out_state(page, live_server, researcher):
    login(page, live_server, researcher)
    page.goto(f"{live_server.url}/accounts/logout/")
    page.click("button[type='submit']")
    assert page.locator("a", has_text="Sign in").is_visible()


def test_admin_tools_visible_for_admin(page, live_server, db):
    User = get_user_model()
    admin = User()
    admin.email = "admin@example.com"
    admin.is_active = True
    admin.admin = True
    admin.is_staff = True
    admin.is_superuser = True
    admin.set_password("adminpass123")
    admin.save()
    login(page, live_server, admin)
    page.goto(f"{live_server.url}/")
    assert page.locator("text=Admin tools").is_visible()


def test_admin_tools_hidden_for_non_admin(page, live_server, researcher):
    login(page, live_server, researcher)
    page.goto(f"{live_server.url}/")
    assert not page.locator("text=Admin tools").is_visible()
