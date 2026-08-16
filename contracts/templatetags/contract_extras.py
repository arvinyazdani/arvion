import re

from django import template
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def contract_terms_html(value):
    """Render supplied legal text with semantic Persian article hierarchy."""
    if not value:
        return ""
    rendered = []
    for line in str(value).replace("\r\n", "\n").split("\n"):
        text = line.strip()
        if not text:
            continue
        escaped = conditional_escape(text)
        if re.match(r"^ماده\s+[۰-۹0-9]+", text):
            rendered.append(format_html("<h3 class=\"legal-article-title\">{}</h3>", escaped))
        elif re.match(r"^[۰-۹0-9]+\s*[-ـ–]\s*[۰-۹0-9]+", text):
            number, body = re.split(r"\s*[-ـ–]\s*", text, maxsplit=1)
            rendered.append(format_html("<p class=\"legal-item\"><b>{}</b>{}</p>", conditional_escape(number), conditional_escape(body)))
        else:
            rendered.append(format_html("<p class=\"legal-paragraph\">{}</p>", escaped))
    return mark_safe("".join(rendered))
