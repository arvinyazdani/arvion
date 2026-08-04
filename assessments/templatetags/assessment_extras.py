import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def inline_code(value):
    """Escape question text, then mark backtick fragments as ASCII code."""
    safe_text = escape(value or "")
    return mark_safe(re.sub(r"`([^`]+)`", r'<code class="inline-code" data-ascii>\1</code>', safe_text))
