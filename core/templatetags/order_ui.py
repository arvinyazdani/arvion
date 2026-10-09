from urllib.parse import urlencode

from django import template
from django.urls import reverse

from core.order_paths import parse_choices, start_url, ADDONS

register = template.Library()


@register.filter
def order_phone(value):
    from core.sms.backends import normalize_iran_mobile
    try:
        return "+" + normalize_iran_mobile(value)
    except ValueError:
        return ""

SERVICE_TOPICS = {"corporate-website-design": "corporate", "ecommerce-platform": "ecommerce",
                  "custom-web-application": "other", "digital-product-consulting": "other"}


@register.simple_tag
def order_entry(topic="", service=""):
    if service == "maintenance-and-growth":
        return start_url("", addons="support")
    return start_url(topic or SERVICE_TOPICS.get(service, ""))


@register.simple_tag(takes_context=True)
def demo_order_context(context, demo):
    choices = parse_choices(context["request"].GET)
    choices["type"] = demo.category
    return {"action": reverse("project_start") + "?" + urlencode({**choices, "sample": demo.slug}),
            "query": urlencode(choices), "addons": [(key, fa if context.get("lang") == "fa" else en)
                                                        for key, fa, en in ADDONS],
            "selected": choices.get("addons", "").split(",")}
