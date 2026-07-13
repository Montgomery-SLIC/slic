from tests.e2e.conftest import login

def test_home_page_loads(page, live_server):
    page.goto(f"{live_server.url}/")
    assert "SLIC" in page.title()


def test_contact_page_loads(page, live_server):
    page.goto(f"{live_server.url}/contact/")
    assert "Contact" in page.content()


def test_documentation_page_loads(page, live_server):
    page.goto(f"{live_server.url}/documentation/")
    assert page.locator(".docs").is_visible()


def test_bug_report_form_has_textarea(page, live_server):
    page.goto(f"{live_server.url}/bug-report/")
    assert page.locator("textarea[name='report']").is_visible()


def test_bug_report_submission(page, live_server):
    page.goto(f"{live_server.url}/bug-report/")
    page.fill("textarea[name='report']", "Something is broken")
    page.click("input[type='submit']")
    assert "Thank you" in page.content()


def test_footer_bug_report_link(page, live_server):
    page.goto(f"{live_server.url}/")
    page.click("a[href*='bug-report']")
    assert "/bug-report/" in page.url


def test_navbar_home_link(page, live_server):
    page.goto(f"{live_server.url}/contact/")
    page.click("a.navbar-brand")
    assert page.url == f"{live_server.url}/"