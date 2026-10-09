"""Presentation orchestration around existing forms and demo submission service."""
from urllib.parse import parse_qs, urlencode, urlsplit

from django.shortcuts import redirect
from django.urls import reverse

from projects.models import DemoTemplate
from projects.demo_briefs import brief_fields
from .order_paths import ADDONS, CONSULTATION, TOPIC_BY_KEY, crm_choices, parse_choices, topic_cards


def final_form_url(choices, demo_token=""):
    topic = TOPIC_BY_KEY.get(choices.get("type"))
    form = topic.form_name if topic else "leads:contact"
    # Consultation should not ask for an entire specialist specification.
    if choices.get("consult") == "1":
        form = "leads:contact"
    url = reverse(form)
    if form in {"crm_orders:create", "clinic_orders:create"}:
        url = "/fa/" + url.split("/", 2)[2]
    params = dict(choices)
    if demo_token:
        params["demo"] = demo_token
    return url + ("?" + urlencode(params) if params else "")


def gateway_context(request, lang):
    choices = parse_choices(request.GET)
    topic = TOPIC_BY_KEY.get(choices.get("type"))
    cards = topic_cards(lang)
    selected = next((card for card in cards if topic and card["key"] == topic.key), None)
    demos = list(DemoTemplate.objects.filter(category=topic.key, is_active=True)) if topic and topic.key not in {"crm", "other"} else []
    return {"order_topics": cards, "order_topic": selected, "order_choices": choices,
            "order_demos": demos, "order_addons": [(key, fa if lang == "fa" else en) for key, fa, en in ADDONS],
            "order_consultation": CONSULTATION[0 if lang == "fa" else 1],
            "order_modules": crm_choices(lang)[0] if topic and topic.key == "crm" else (),
            "order_extensions": crm_choices(lang)[1] if topic and topic.key == "crm" else (),
            "order_brief": [field for field in brief_fields("corporate", lang) if field["key"] != "timing"] if topic and topic.key == "other" else (),
            "order_final_url": final_form_url(choices)}


def gateway_get_destination(request):
    choices = parse_choices(request.GET)
    if request.GET.get("go") == "form" or choices.get("consult") == "1":
        return final_form_url(choices)
    if request.GET.get("go") != "preview":
        return None
    demo = DemoTemplate.objects.filter(slug=request.GET.get("sample", "")[:100],
                                       category=choices.get("type", ""), is_active=True).first()
    if not demo:
        return None
    return reverse("projects:demo_preview", args=[demo.slug]) + "?" + urlencode(choices)


def submit_existing_demo(request):
    """Delegate unchanged idempotency, validation and session checks, never copy them."""
    from projects.views.projects import DemoConfigureView
    merged = request.GET.copy()
    for key in ("brief_goal", "brief_scope", "brief_content", "brief_timing"):
        if key in request.POST:
            merged[key] = request.POST[key]
    if "order_addons" in request.POST:
        merged.setlist("addons", request.POST.getlist("order_addons"))
    choices = parse_choices(merged)
    demo = DemoTemplate.objects.filter(slug=request.GET.get("sample", "")[:100],
                                       category=choices.get("type", ""), is_active=True).first()
    if not demo:
        return redirect("project_start")
    response = DemoConfigureView.as_view()(request, slug=demo.slug)
    location = response.get("Location", "")
    if response.status_code == 302 and urlsplit(location).path == reverse("leads:contact"):
        token = parse_qs(urlsplit(location).query).get("demo", [""])[0]
        return redirect(final_form_url(choices, token))
    return response
