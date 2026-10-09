"""Read-only order presentation; customer identity stays in final domain forms."""
from core.order_paths import ADDONS, TOPIC_BY_KEY, crm_choices, parse_choices, request_type
from projects.demo_briefs import brief_fields


def summary_lines(request, lang):
    choices = parse_choices(request.GET)
    topic = TOPIC_BY_KEY.get(choices.get("type"))
    if not topic:
        return []
    lines = [getattr(topic, "title_" + lang)]
    addon_labels = {key: fa if lang == "fa" else en for key, fa, en in ADDONS}
    lines.extend(addon_labels[key] for key in choices.get("addons", "").split(",") if key in addon_labels)
    modules, extensions = crm_choices(lang)
    for field, labels in (("modules", dict(modules)), ("extensions", dict(extensions))):
        lines.extend(labels[key] for key in choices.get(field, "").split(",") if key in labels)
    for field in brief_fields(topic.key if topic.key not in {"crm", "other"} else "corporate", lang):
        value = choices.get("brief_" + field["key"])
        label = dict(field["options"]).get(value)
        if label:
            lines.append(field["label"] + ": " + label)
    return lines


def specialist_initial(request):
    """Only put a readable non-personal selection summary in an existing field."""
    lines = summary_lines(request, "fa")
    # A demo is readable only through the existing session-bound validator.
    from leads.views.contact import _session_demo_selection
    selection = _session_demo_selection(request)
    if selection:
        from projects.demo_snapshots import build_demo_selection_snapshot
        snapshot = build_demo_selection_snapshot(selection)
        lines.extend(str(snapshot[key]) for key in ("template_title_fa", "theme_fa", "personality_fa") if snapshot.get(key))
        lines.extend(snapshot.get("features_fa", []))
        lines.extend(snapshot.get("brief_fa", []))
    return {"additional_notes": "انتخاب‌های اولیه (نمونه، نه تعهد):\n" + "\n".join(lines)} if lines else {}


def lead_initial(request, initial, lang):
    choices = parse_choices(request.GET)
    if "type" not in choices and not choices.get("consult") and not choices.get("addons"):
        return initial
    initial["request_type"] = request_type(choices)
    from services.models import Service
    topic = TOPIC_BY_KEY.get(choices.get("type"))
    slug = "custom-web-application" if initial["request_type"] == "webapp" else topic.service_slug if topic else ""
    if slug and not choices.get("consult"):
        service = Service.objects.filter(slug=slug, is_active=True).first()
        if service:
            initial["service"] = service
    lines = summary_lines(request, lang)
    if lines:
        heading = "انتخاب‌های اولیه (نمونه، نه تعهد):" if lang == "fa" else "Initial choices (sample, not a commitment):"
        initial["message"] = (initial.get("message", "") + "\n" + heading + "\n" + "\n".join(lines)).strip()
    return initial
