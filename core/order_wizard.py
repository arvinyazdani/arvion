"""Safe server catalogue for the progressively enhanced /start/ wizard.

Only public labels and closed preferences. No customer/brand text, session
identifiers, storage writes or model changes. JSON is emitted with json_script.
"""
from django.urls import reverse

from core.order_paths import ADDONS, CONSULTATION, LOOKS, PALETTES, TOPICS, crm_choices, parse_choices
from projects.demo_labels import CATEGORY_FEATURE_KEYS, demo_config_labels


def wizard_catalogue(query, lang):
    offset = 1 if lang == "fa" else 2
    modules, extensions = crm_choices(lang)
    topics = []
    for topic in TOPICS:
        features = (demo_config_labels(lang, topic.key)["features"]
                    if topic.key in CATEGORY_FEATURE_KEYS else
                    modules if topic.key == "crm" else ())
        topics.append({"key": topic.key, "title": getattr(topic, "title_" + lang),
                       "features": list(features),
                       "extensions": list(extensions) if topic.key == "crm" else [],
                       "specialist_fa": topic.key in {"clinic", "crm"}})
    return {"lang": lang, "initial": parse_choices(query), "topics": topics,
            "palettes": [(row[0], row[offset]) for row in PALETTES],
            "looks": [(row[0], row[offset]) for row in LOOKS],
            "addons": [(row[0], row[offset]) for row in ADDONS],
            "consultation": CONSULTATION[0 if lang == "fa" else 1],
            "continue_url": reverse("project_start"),
            "gallery_url": reverse("projects:demo_gallery")}


def submit_wizard(request):
    """Adapt closed scene choices to the existing session-safe demo hand-off.

    Brand input is deliberately not read. The existing gallery vocabulary is
    not reinterpreted as order-scene preferences: its neutral carrier is used
    only for the selected functional modules; palette/look travel separately.
    """
    from urllib.parse import urlencode, urlsplit, parse_qs
    from django.http import QueryDict
    from django.shortcuts import redirect
    from projects.models import DemoTemplate
    from projects.views.projects import DemoConfigureView
    from core.order_gateway import final_form_url
    choices = parse_choices(request.POST)
    topic = choices.get("type")
    if not topic:
        return redirect("project_start")
    if topic in {"crm", "other"} or choices.get("consult") == "1":
        return redirect(final_form_url(choices))
    allowed = set(CATEGORY_FEATURE_KEYS.get(topic, ()))
    features = sorted(set(request.POST.getlist("features")) & allowed)
    if not features:
        return redirect(final_form_url(choices))
    demo = DemoTemplate.objects.filter(category=topic, is_active=True).order_by("display_order", "pk").first()
    if not demo:
        return redirect(reverse("project_start") + "?" + urlencode({**choices, "wizard_error": "unavailable"}))
    original = request.POST
    payload = QueryDict(mutable=True)
    payload.update({"submission_token": original.get("submission_token", "")[:64],
                    "theme": "warm", "personality": "minimal"})
    payload.setlist("features", features)
    request.POST = payload
    try:
        response = DemoConfigureView.as_view()(request, slug=demo.slug)
    finally:
        request.POST = original
    location = response.get("Location", "")
    if response.status_code == 302 and urlsplit(location).path == reverse("leads:contact"):
        token = parse_qs(urlsplit(location).query).get("demo", [""])[0]
        return redirect(final_form_url(choices, token))
    # Do not send the visitor to an unrelated gallery error/retry screen.
    return redirect(reverse("project_start") + "?" + urlencode({**choices, "wizard_error": "retry"}))
