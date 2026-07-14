import json
import urllib.parse
import urllib.request

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe
from django.core.mail import EmailMessage
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import resolve, Resolver404
from django.utils.translation import override as lang_override
import markdown as md


def _render_md(filename):
    path = settings.BASE_DIR / filename
    text = path.read_text(encoding='utf-8')
    return mark_safe(md.markdown(text, extensions=['extra', 'nl2br']))


def contact_us_view(request):
    return render(request, 'pages/contact_us.html', {'content': _render_md('docs/CONTACT_US.md')})


def documentation_view(request):
    return render(request, 'pages/documentation.html', {'content': _render_md('docs/USER_DOCUMENTATION.md')})


def bug_report_new(request):
    return render(request, 'bug_reports/new.html')


@require_POST
def switch_language(request):
    """Language switcher that avoids Django's translate_url / active-language mismatch bug

    set_language resolves `next` using whatever language LocaleMiddleware activated
    for the /i18n/setlang/ URL (which has no prefix). If the cookie and the URL
    prefix disagree, resolve() raises Resolver404 and the user gets stuck

    This view sidesteps that entirely: it strips any non-default language prefix
    from `next`, prepends the new one, sets the cookie, and redirects
    """
    lang_code = request.POST.get('language', settings.LANGUAGE_CODE)
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/'

    # Safety check - reject cross-site redirects
    if not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = '/'

    # Validate the requested language
    valid_codes = {code for code, _ in settings.LANGUAGES}
    if lang_code not in valid_codes:
        lang_code = settings.LANGUAGE_CODE

    # Strip any existing non-default language prefix (e.g. /da/ or /fr/)
    default = settings.LANGUAGE_CODE
    for code, _ in settings.LANGUAGES:
        if code != default and next_url.startswith(f'/{code}/'):
            next_url = '/' + next_url[len(f'/{code}/'):]
            break
        if code != default and next_url == f'/{code}':
            next_url = '/'
            break

    # Prepend the new prefix only if the prefixed URL actually resolves
    # Participant pages are outside i18n_patterns, so they have no language
    # prefix; the cookie controls their language and next_url stays as-is
    if lang_code != default:
        candidate = f'/{lang_code}{next_url}'
        with lang_override(lang_code):
            try:
                resolve(candidate)
                next_url = candidate
            except Resolver404:
                pass  # not an i18n_patterns URL - keep base URL, cookie is enough

    # Final safety check after all URL transformations - if/else form so CodeQL
    # recognises url_has_allowed_host_and_scheme as a sanitizer guarding the sink
    if url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        response = redirect(next_url)
    else:
        response = redirect('/')
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        lang_code,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        path=settings.LANGUAGE_COOKIE_PATH,
        domain=settings.LANGUAGE_COOKIE_DOMAIN,
        secure=settings.LANGUAGE_COOKIE_SECURE,
        httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
        samesite=settings.LANGUAGE_COOKIE_SAMESITE,
    )
    return response


def bug_report_submit(request):
    if request.method == 'POST':
        # reCAPTCHA validation - skip if no private key configured (dev / test)
        if getattr(settings, 'RECAPTCHA_PRIVATE_KEY', ''):
            captcha_response = request.POST.get('g-recaptcha-response', '')
            if not captcha_response:
                return render(request, 'bug_reports/new.html', {
                    'error': 'Please complete the reCAPTCHA.',
                })
            try:
                _payload = urllib.parse.urlencode({
                    'secret': settings.RECAPTCHA_PRIVATE_KEY,
                    'response': captcha_response,
                    'remoteip': request.META.get('REMOTE_ADDR', ''),
                }).encode()
                with urllib.request.urlopen(
                    'https://www.google.com/recaptcha/api/siteverify', _payload, timeout=5
                ) as _resp:
                    _result = json.loads(_resp.read())
            except Exception:
                _result = {}
            if not _result.get('success'):
                return render(request, 'bug_reports/new.html', {
                    'error': 'reCAPTCHA validation failed. Please try again.',
                })

        report = request.POST.get('report', '')
        email = request.POST.get('email', '')
        msg = EmailMessage(
            subject='[BUG REPORT]',
            body=report,
            from_email=getattr(settings, 'SERVER_EMAIL', 'root@localhost'),
            to=[settings.BUG_REPORT_EMAIL],
            reply_to=[email] if email else [],
        )
        msg.send(fail_silently=True)
    return render(request, 'bug_reports/received.html')

urlpatterns = [
    path('i18n/setlang/', switch_language, name='set_language'),
    # Participant routes - no locale prefix needed
    path('', include('responses.urls')),
    # Click response XHR endpoint - no locale prefix
    path('click-responses/', include('responses.click_urls')),
]

urlpatterns += i18n_patterns(
    # Home page inside i18n_patterns so LocaleMiddleware uses the URL prefix for non-English
    # locales (e.g. /da/, /fr/) rather than ignoring the cookie for bare /.
    path('', TemplateView.as_view(template_name='pages/home.html'), name='root'),
    path('django-admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('accounts.urls')),
    path('experiments/', include('experiments.urls')),
    path('tasks/', include('tasks.urls')),
    path('contact/', contact_us_view, name='contact_us'),
    path('documentation/', documentation_view, name='documentation'),
    path('bug-report/', bug_report_new, name='bug_report_new'),
    path('bug-report/submit/', bug_report_submit, name='bug_report_submit'),
    prefix_default_language=False,
)

if not settings.X_ACCEL_REDIRECT:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Serve doc images at /images/ to match paths hardcoded in USER_DOCUMENTATION.md
    urlpatterns += static('/images/', document_root=settings.BASE_DIR / 'static' / 'images')
