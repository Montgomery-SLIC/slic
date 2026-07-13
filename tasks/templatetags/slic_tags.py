from django import template
from django.utils.safestring import mark_safe
import bleach
import markdown as md

register = template.Library()

# Tags and attributes that markdown legitimately produces.
# Anything not listed here is stripped before the output is marked safe.
_ALLOWED_TAGS = frozenset({
    'a', 'abbr', 'b', 'blockquote', 'br', 'code', 'del', 'em',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i',
    'li', 'ol', 'p', 'pre', 's', 'strong', 'sub', 'sup',
    'table', 'tbody', 'td', 'th', 'thead', 'tr', 'ul',
})

_ALLOWED_ATTRS = {
    'a':    ['href', 'title'],
    'td':   ['align', 'colspan', 'rowspan'],
    'th':   ['align', 'colspan', 'rowspan'],
    'code': ['class'],
}


@register.filter(name='markdown')
def markdown_filter(value):
    if not value:
        return ''
    raw_html = md.markdown(str(value), extensions=['extra', 'nl2br'])
    clean_html = bleach.clean(raw_html, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS, strip=True)
    return mark_safe(clean_html)


@register.simple_tag
def range_n(n):
    try:
        return range(1, int(n) + 1)
    except (TypeError, ValueError):
        return range(0)


@register.filter(name='class_name')
def class_name_filter(obj):
    return type(obj).__name__
