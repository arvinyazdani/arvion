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
