"""Bilingual, non-sensitive snapshot of a DemoSelection.

Shared by `management_portal.cases` (the "Demo selection" section on a
CustomerCase) and `leads.form_draft_service` (an authenticated customer's
saved form draft), so both freeze the exact same shape from one place
instead of a private cross-app import. Deliberately excludes
`public_token`, `session_key`, and `submission_token` — those identify one
anonymous browser session/request and must never reach a staff- or
account-facing record.
"""

from .demo_labels import CATEGORY_LABELS_EN, demo_config_labels
from .models import DemoTemplate

DASH = "—"
# Generous relative to what the demo configurator's own client-side code
# already enforces (a 48-character brand cap) — this is only a defensive
# backstop against a malformed/oversized stored value, never a real limit
# on anything the trusted client flow can actually produce, so it changes
# nothing for existing valid data.
_MAX_BRAND_LENGTH = 200
_MAX_FEATURES = 20


def _safe_key(value):
    """A dict key used only for label lookups: must be a plain string, or
    lookups below would either crash (unhashable types) or silently match
    nothing useful — never raise on malformed stored data."""
    return value if isinstance(value, str) else ""


def build_demo_selection_snapshot(selection):
    """A frozen, human-readable copy of a Lead's demo choice.

    Stores resolved bilingual labels rather than raw keys or a live
    reference, so the case's own record stays fully readable even after
    the underlying (anonymous) DemoSelection row is eventually removed by
    `cleanup_demo_selections`, and even if the label wording changes later.
    Deliberately excludes `public_token` and `session_key` — those identify
    one anonymous browser session and must never reach a staff-facing case
    record.
    """
    template = selection.template
    values = selection.selections or {}
    labels_fa = demo_config_labels("fa")
    labels_en = demo_config_labels("en")
    theme_key = _safe_key(values.get("theme", ""))
    personality_key = _safe_key(values.get("personality", ""))
    raw_features = values.get("features")
    feature_keys = (
        [key for key in raw_features if isinstance(key, str)][:_MAX_FEATURES]
        if isinstance(raw_features, list) else []
    )
    feature_lookup_fa = dict(labels_fa["features"])
    feature_lookup_en = dict(labels_en["features"])
    raw_brand = values.get("brand")
    brand = raw_brand.strip()[:_MAX_BRAND_LENGTH] if isinstance(raw_brand, str) else ""
    return {
        "template_title_fa": template.title_fa,
        "template_title_en": template.title_en,
        "category_fa": dict(DemoTemplate.CATEGORY_CHOICES).get(template.category, template.category),
        "category_en": CATEGORY_LABELS_EN.get(template.category, template.category),
        "brand": brand or template.fictional_brand_fa,
        "theme_fa": dict(labels_fa["themes"]).get(theme_key) or DASH,
        "theme_en": dict(labels_en["themes"]).get(theme_key) or DASH,
        "personality_fa": dict(labels_fa["personalities"]).get(personality_key) or DASH,
        "personality_en": dict(labels_en["personalities"]).get(personality_key) or DASH,
        "features_fa": [feature_lookup_fa.get(key, key) for key in feature_keys],
        "features_en": [feature_lookup_en.get(key, key) for key in feature_keys],
        "demo_template_slug": template.slug,
    }
