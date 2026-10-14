"""Read-only order presentation; customer identity stays in final domain forms."""
from core.order_paths import ADDONS, LOOKS, PALETTES, TOPIC_BY_KEY, crm_choices, parse_choices, request_type
from projects.demo_briefs import brief_fields


def summary_lines(request, lang):
    choices = parse_choices(request.GET)
    topic = TOPIC_BY_KEY.get(choices.get("type"))
    if not topic:
        return []
    lines = [getattr(topic, "title_" + lang)]
    for key, options, heading in (("palette", PALETTES, "رنگ" if lang == "fa" else "Colour"),
                                   ("look", LOOKS, "حال‌وهوا" if lang == "fa" else "Look")):
        labels = {row[0]: row[1 if lang == "fa" else 2] for row in options}
        if choices.get(key) in labels:
            lines.append(heading + ": " + labels[choices[key]])
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
    choices = parse_choices(request.GET)
    lines = summary_lines(request, "fa")
    # A demo is readable only through the existing session-bound validator.
    from leads.views.contact import _session_demo_selection
    selection = _session_demo_selection(request)
    if selection:
        from projects.demo_snapshots import build_demo_selection_snapshot
        snapshot = build_demo_selection_snapshot(selection)
        if choices.get("palette") and choices.get("look"):
            lines.append("مرجع فنی امکانات (نه طرح نهایی): " + snapshot["template_title_fa"])
        else:
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
        if choices.get("palette") and choices.get("look"):
            # A neutral demo record carries capabilities only. Its template
            # was not a visual template the studio visitor explicitly chose.
            prefix = "نمونه انتخاب‌شده:" if lang == "fa" else "Selected demo:"
            replacement = "مرجع فنی امکانات (نه طرح انتخابی):" if lang == "fa" else "Functional reference (not a chosen visual template):"
            initial["message"] = initial.get("message", "").replace(prefix, replacement, 1)
        initial["message"] = (initial.get("message", "") + "\n" + heading + "\n" + "\n".join(lines)).strip()
    return initial


def calculator_initial(request, initial, lang):
    """Carry only allow-listed, non-identifying estimate choices into a lead."""
    if request.GET.get("estimate") != "1":
        return initial
    from core.cost_calculator_data import PRODUCTS, TEAM_FACTORS
    product = PRODUCTS.get(request.GET.get("product", ""))
    team = TEAM_FACTORS.get(request.GET.get("team", ""))
    if not product or not team:
        return initial
    bounds = {"roles": (1, 20), "integrations": (0, 20), "erp": (0, 5), "mobile": (0, 1), "legal": (0, 1), "maintenance": (10, 20)}
    values = {}
    for name, (minimum, maximum) in bounds.items():
        try:
            values[name] = max(minimum, min(maximum, int(request.GET.get(name, "0"))))
        except (TypeError, ValueError):
            return initial
    product_label = product["label"][0 if lang == "fa" else 1]
    team_label = team["label"][0 if lang == "fa" else 1]
    if lang == "fa":
        lines = [f"محصول: {product_label}", f"نقش‌های کاربری: {values['roles']}",
                 f"اتصال‌های معمولی: {values['integrations']}", f"اتصال ERP: {values['erp']}",
                 f"اپ موبایل: {'بله' if values['mobile'] else 'خیر'}",
                 f"الزامات حریم/حقوقی: {'بله' if values['legal'] else 'خیر'}",
                 f"نوع تیم: {team_label}", f"فرض نگهداری سالانه: {values['maintenance']}%",
                 "این‌ها انتخاب‌های اولیه از محاسبه‌گرند، نه قیمت یا تعهد پروژه."]
        heading = "خلاصه انتخاب‌های محاسبه‌گر (پیش‌نویس):"
    else:
        lines = [f"Product: {product_label}", f"User roles: {values['roles']}",
                 f"Standard integrations: {values['integrations']}", f"ERP integrations: {values['erp']}",
                 f"Mobile app: {'Yes' if values['mobile'] else 'No'}",
                 f"Privacy/legal scope: {'Yes' if values['legal'] else 'No'}",
                 f"Team scenario: {team_label}", f"Annual maintenance assumption: {values['maintenance']}%",
                 "These are initial calculator choices, not a project price or commitment."]
        heading = "Cost calculator selections (draft):"
    existing = initial.get("message", "").strip()
    initial["message"] = (existing + ("\n\n" if existing else "") + heading + "\n" + "\n".join(lines)).strip()
    return initial
