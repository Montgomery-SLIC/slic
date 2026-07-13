"""
Tests for internationalization: home page at each language-prefixed URL,
and the switch_language view (redirect targets, cookie, safety checks).
"""
from django.test import TestCase


class TestHomePageLocalization(TestCase):
    """Home page is served at /, /da/, and /fr/ with the correct translated content."""

    def test_root_returns_200(self):
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_danish_prefix_returns_200(self):
        self.assertEqual(self.client.get('/da/').status_code, 200)

    def test_french_prefix_returns_200(self):
        self.assertEqual(self.client.get('/fr/').status_code, 200)

    def test_root_shows_english_heading(self):
        self.assertContains(self.client.get('/'), 'Welcome to SLIC')

    def test_danish_prefix_shows_danish_heading(self):
        self.assertContains(self.client.get('/da/'), 'Velkommen til SLIC')

    def test_french_prefix_shows_french_heading(self):
        self.assertContains(self.client.get('/fr/'), 'Bienvenue sur SLIC')

    def test_root_does_not_bleed_danish_content(self):
        self.assertNotContains(self.client.get('/'), 'Velkommen til SLIC')

    def test_home_accessible_without_login(self):
        # All three URL forms must not redirect to login
        for url in ('/', '/da/', '/fr/'):
            with self.subTest(url=url):
                self.assertNotEqual(self.client.get(url).status_code, 302)


class TestSwitchLanguageView(TestCase):
    """switch_language redirects to the correct language-prefixed URL and sets the cookie."""

    URL = '/i18n/setlang/'

    def _switch(self, language, next_url):
        return self.client.post(self.URL, {'language': language, 'next': next_url})

    # Home page - this was the originally broken case
    def test_home_to_danish_redirects_to_da_prefix(self):
        response = self._switch('da', '/')
        self.assertRedirects(response, '/da/', fetch_redirect_response=False)

    def test_home_to_french_redirects_to_fr_prefix(self):
        response = self._switch('fr', '/')
        self.assertRedirects(response, '/fr/', fetch_redirect_response=False)

    def test_da_home_to_english_strips_prefix(self):
        response = self._switch('en', '/da/')
        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def test_fr_home_to_english_strips_prefix(self):
        response = self._switch('en', '/fr/')
        self.assertRedirects(response, '/', fetch_redirect_response=False)

    # Researcher pages (inside i18n_patterns)
    def test_english_experiments_to_danish(self):
        response = self._switch('da', '/experiments/')
        self.assertRedirects(response, '/da/experiments/', fetch_redirect_response=False)

    def test_danish_experiments_to_english(self):
        response = self._switch('en', '/da/experiments/')
        self.assertRedirects(response, '/experiments/', fetch_redirect_response=False)

    def test_danish_page_to_french_swaps_prefix(self):
        response = self._switch('fr', '/da/experiments/')
        self.assertRedirects(response, '/fr/experiments/', fetch_redirect_response=False)

    # Participant pages (outside i18n_patterns - cookie only, no URL prefix)
    def test_participant_page_gets_no_prefix(self):
        response = self._switch('da', '/my-study/home/')
        self.assertRedirects(response, '/my-study/home/', fetch_redirect_response=False)

    # Cookie
    def test_sets_django_language_cookie(self):
        self._switch('da', '/')
        self.assertEqual(self.client.cookies['django_language'].value, 'da')

    def test_cookie_updates_when_switching_back(self):
        self._switch('da', '/')
        self._switch('en', '/da/')
        self.assertEqual(self.client.cookies['django_language'].value, 'en')

    # Safety
    def test_invalid_language_falls_back_to_default(self):
        response = self._switch('xx', '/')
        self.assertRedirects(response, '/', fetch_redirect_response=False)
        self.assertEqual(self.client.cookies['django_language'].value, 'en')

    def test_cross_site_next_url_is_rejected(self):
        response = self._switch('da', 'http://evil.example.com/steal')
        location = response['Location']
        self.assertNotIn('evil.example.com', location)

    def test_get_request_returns_405(self):
        self.assertEqual(self.client.get(self.URL).status_code, 405)
