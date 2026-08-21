import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

from core.i18n_numbers import persian_digits

register = template.Library()


@register.filter
def group_digits(value):
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return value


@register.filter
def fa_digits(value):
    """Render presentation-only numerals with Persian glyphs."""
    return persian_digits(value)


@register.filter
def group_digits_fa(value):
    """Group an integer and render the result with Persian numerals."""
    return persian_digits(group_digits(value))


@register.filter
def inline_code(value):
    """Escape question text, then mark backtick fragments as ASCII code."""
    safe_text = escape(value or "")
    return mark_safe(re.sub(r"`([^`]+)`", r'<code class="inline-code" data-ascii>\1</code>', safe_text))
