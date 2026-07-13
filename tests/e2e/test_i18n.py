"""
End-to-end tests for language switching via the navbar flag dropdown.

These tests specifically cover the home page, which was previously broken:
LocaleMiddleware forced English for bare / regardless of cookie when
prefix_default_language=False, so the home page never translated.
The fix was to move the home page route inside i18n_patterns so that
switching to Danish redirects to /da/ (URL-driven language, not cookie-driven).
"""


def test_home_page_loads_in_english(page, live_server):
    page.goto(f"{live_server.url}/")
    assert "Welcome to SLIC" in page.content()


def test_switch_to_danish_on_home_changes_url(page, live_server):
    page.goto(f"{live_server.url}/")
    page.locator("#navbar-locale-link").click()
    page.locator("form:has(input[name='language'][value='da']) button").click()
    page.wait_for_load_state("networkidle")
    assert "/da/" in page.url


def test_switch_to_danish_on_home_translates_content(page, live_server):
    page.goto(f"{live_server.url}/")
    page.locator("#navbar-locale-link").click()
    page.locator("form:has(input[name='language'][value='da']) button").click()
    page.wait_for_load_state("networkidle")
    assert "Velkommen til SLIC" in page.content()


def test_switch_to_french_on_home_changes_url(page, live_server):
    page.goto(f"{live_server.url}/")
    page.locator("#navbar-locale-link").click()
    page.locator("form:has(input[name='language'][value='fr']) button").click()
    page.wait_for_load_state("networkidle")
    assert "/fr/" in page.url


def test_switch_to_french_on_home_translates_content(page, live_server):
    page.goto(f"{live_server.url}/")
    page.locator("#navbar-locale-link").click()
    page.locator("form:has(input[name='language'][value='fr']) button").click()
    page.wait_for_load_state("networkidle")
    assert "Bienvenue sur SLIC" in page.content()


def test_switch_back_to_english_from_danish_home(page, live_server):
    page.goto(f"{live_server.url}/da/")
    page.locator("#navbar-locale-link").click()
    page.locator("form:has(input[name='language'][value='en']) button").click()
    page.wait_for_load_state("networkidle")
    assert "/da/" not in page.url
    assert "Welcome to SLIC" in page.content()


def test_language_prefix_persists_when_navigating_to_contact(page, live_server):
    # Danish home → click Contact in navbar → should land on /da/contact/
    page.goto(f"{live_server.url}/da/")
    page.locator("nav a[href*='contact']").first.click()
    page.wait_for_load_state("networkidle")
    assert "/da/" in page.url


def test_navbar_home_link_respects_current_language(page, live_server):
    # When on the Danish home page, clicking the brand link should stay on /da/
    page.goto(f"{live_server.url}/da/")
    page.locator("a.navbar-brand").click()
    page.wait_for_load_state("networkidle")
    assert "/da/" in page.url
