import re

from django import template
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe

from core.i18n_numbers import persian_digits

register = template.Library()


@register.filter
def persian_amount(value):
    """Render an IRR amount in readable Persian three-digit groups."""
    try:
        return persian_digits(f"{int(value):,}")
    except (TypeError, ValueError):
        return ""


@register.filter
def contract_terms_html(value):
    """Render legal terms as a readable, article-by-article disclosure list."""
    if not value:
        return ""
    preamble, articles, current = [], [], None
    for line in str(value).replace("\r\n", "\n").split("\n"):
        text = line.strip()
        if not text:
            continue
        if re.match(r"^ماده\s+[۰-۹0-9]+", text):
            current = {"title": text, "items": []}
            articles.append(current)
            continue
        target = current["items"] if current else preamble
        if re.match(r"^[۰-۹0-9]+\s*[-ـ–]\s*[۰-۹0-9]+", text):
            number, body = re.split(r"\s*[-ـ–]\s*", text, maxsplit=1)
            target.append(format_html(
                "<p class=\"legal-item\"><b>{}</b><span>{}</span></p>",
                conditional_escape(number), conditional_escape(body),
            ))
        else:
            target.append(format_html("<p class=\"legal-paragraph\">{}</p>", conditional_escape(text)))
    rendered = [format_html("<div class=\"legal-preamble\">{}</div>", mark_safe("".join(preamble)))] if preamble else []
    for index, article in enumerate(articles, 1):
        body = mark_safe("".join(article["items"]))
        rendered.append(format_html(
            "<details class=\"legal-article\" data-legal-article><summary><span class=\"legal-article-number\">{}</span><span class=\"legal-article-title\">{}</span><span class=\"legal-article-toggle\" aria-hidden=\"true\">نمایش</span></summary><div class=\"legal-article-content\">{}<button class=\"legal-close\" type=\"button\" data-legal-close>بستن ماده <span aria-hidden=\"true\">↑</span></button></div></details>",
            f"{index:02d}", conditional_escape(article["title"]), body,
        ))
    return mark_safe("".join(rendered))
