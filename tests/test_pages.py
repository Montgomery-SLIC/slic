"""
Tests for static/content pages: home, contact, documentation, bug report.
All pages must be accessible without login.
"""
from django.core import mail
from django.test import TestCase, override_settings
from tasks.templatetags.slic_tags import markdown_filter


class TestHomePage(TestCase):
    def test_home_returns_200(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_home_contains_slic(self):
        response = self.client.get('/')
        self.assertContains(response, 'SLIC')

    def test_home_accessible_without_login(self):
        response = self.client.get('/')
        self.assertNotEqual(response.status_code, 302)


class TestContactPage(TestCase):
    def test_contact_returns_200(self):
        response = self.client.get('/contact/')
        self.assertEqual(response.status_code, 200)

    def test_contact_contains_contact_details(self):
        response = self.client.get('/contact/')
        self.assertContains(response, 'Dr Chris Montgomery')

    def test_contact_accessible_without_login(self):
        response = self.client.get('/contact/')
        self.assertNotEqual(response.status_code, 302)


class TestDocumentationPage(TestCase):
    def test_documentation_returns_200(self):
        response = self.client.get('/documentation/')
        self.assertEqual(response.status_code, 200)

    def test_documentation_contains_guide_heading(self):
        response = self.client.get('/documentation/')
        self.assertContains(response, 'user guide', msg_prefix='Expected guide content in docs page')

    def test_documentation_contains_table_of_contents(self):
        response = self.client.get('/documentation/')
        self.assertContains(response, 'Table of contents')

    def test_documentation_accessible_without_login(self):
        response = self.client.get('/documentation/')
        self.assertNotEqual(response.status_code, 302)


class TestBugReportPage(TestCase):
    def test_bug_report_form_returns_200(self):
        response = self.client.get('/bug-report/')
        self.assertEqual(response.status_code, 200)

    def test_bug_report_form_accessible_without_login(self):
        response = self.client.get('/bug-report/')
        self.assertNotEqual(response.status_code, 302)

    def test_bug_report_form_contains_email_and_details_fields(self):
        response = self.client.get('/bug-report/')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="report"')

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        BUG_REPORT_EMAIL='bugs@example.com',
    )
    def test_bug_report_submit_sends_email(self):
        self.client.post('/bug-report/submit/', {
            'report': 'Something is broken',
            'email': 'tester@example.com',
        })
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('bugs@example.com', mail.outbox[0].to)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_bug_report_submit_sets_reply_to(self):
        self.client.post('/bug-report/submit/', {
            'report': 'test',
            'email': 'reporter@example.com',
        })
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('reporter@example.com', mail.outbox[0].reply_to)

    def test_bug_report_submit_returns_200_with_confirmation(self):
        response = self.client.post('/bug-report/submit/', {
            'report': 'test bug',
            'email': 'tester@example.com',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Thank you')

    def test_bug_report_submit_shows_sent_message(self):
        response = self.client.post('/bug-report/submit/', {
            'report': 'test bug',
            'email': 'tester@example.com',
        })
        self.assertContains(response, 'sent')

    def test_bug_report_submit_without_email_returns_200(self):
        response = self.client.post('/bug-report/submit/', {
            'report': 'bug with no email',
            'email': '',
        })
        self.assertEqual(response.status_code, 200)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_bug_report_submit_without_email_still_sends(self):
        self.client.post('/bug-report/submit/', {
            'report': 'bug with no email',
            'email': '',
        })
        self.assertEqual(len(mail.outbox), 1)

    def test_bug_report_submit_accessible_without_login(self):
        response = self.client.post('/bug-report/submit/', {
            'report': 'test',
            'email': '',
        })
        self.assertNotEqual(response.status_code, 302)

    @override_settings(
        RECAPTCHA_PRIVATE_KEY='test-private-key',
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    )
    def test_bug_report_submit_without_captcha_token_blocks_email(self):
        """When reCAPTCHA is configured, a missing token must prevent the email being sent."""
        self.client.post('/bug-report/submit/', {
            'report': 'Something is broken',
            'email': 'tester@example.com',
            # No g-recaptcha-response
        })
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(RECAPTCHA_PRIVATE_KEY='test-private-key')
    def test_bug_report_submit_without_captcha_token_rerenders_form(self):
        """When reCAPTCHA is configured, a missing token must re-render the bug report form."""
        response = self.client.post('/bug-report/submit/', {
            'report': 'Something is broken',
            'email': 'tester@example.com',
        })
        self.assertContains(response, 'reCAPTCHA')


class TestMarkdownFilter(TestCase):
    def test_script_tags_are_stripped(self):
        result = markdown_filter('<script>alert("xss")</script>')
        self.assertNotIn('<script>', result)
        self.assertNotIn('</script>', result)

    def test_event_handler_attributes_are_stripped(self):
        result = markdown_filter('<a href="#" onclick="alert(1)">click</a>')
        self.assertNotIn('onclick', result)

    def test_javascript_protocol_href_is_stripped(self):
        result = markdown_filter('<a href="javascript:alert(1)">click</a>')
        self.assertNotIn('javascript:', result)

    def test_onerror_on_img_is_stripped(self):
        result = markdown_filter('<img src="x" onerror="alert(1)">')
        self.assertNotIn('onerror', result)

    def test_bold_markdown_is_preserved(self):
        result = markdown_filter('**bold**')
        self.assertIn('<strong>bold</strong>', result)

    def test_italic_markdown_is_preserved(self):
        result = markdown_filter('_italic_')
        self.assertIn('<em>italic</em>', result)

    def test_link_markdown_is_preserved(self):
        result = markdown_filter('[SLIC](https://example.com)')
        self.assertIn('href="https://example.com"', result)
        self.assertIn('SLIC', result)

    def test_empty_string_returns_empty(self):
        self.assertEqual(markdown_filter(''), '')

    def test_none_returns_empty(self):
        self.assertEqual(markdown_filter(None), '')
