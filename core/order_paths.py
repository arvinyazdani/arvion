"""Public order vocabulary. Only bounded, non-personal choices belong here.

No session writes, model dependencies or template dependencies. Existing domain
forms remain the only collectors of customer identity and contact information.
"""
from dataclasses import dataclass
from urllib.parse import urlencode

from django.urls import reverse

from projects.demo_labels import CATEGORY_FEATURE_KEYS, CATEGORY_LABELS_EN, demo_config_labels
from projects.demo_briefs import COMMON, GOALS


@dataclass(frozen=True)
class OrderTopic:
    key: str
    title_fa: str
    title_en: str
    icon: str
    form_name: str = "leads:contact"
    service_slug: str = "corporate-website-design"


TOPICS = (
    OrderTopic("ecommerce", "فروشگاه اینترنتی", CATEGORY_LABELS_EN["ecommerce"], "payment", service_slug="ecommerce-platform"),
    OrderTopic("restaurant", "رستوران و کافه", CATEGORY_LABELS_EN["restaurant"], "services"),
    OrderTopic("clinic", "کلینیک", CATEGORY_LABELS_EN["clinic"], "account", "clinic_orders:create", "custom-web-application"),
    OrderTopic("corporate", "وب‌سایت شرکتی", CATEGORY_LABELS_EN["corporate"], "globe"),
    OrderTopic("portfolio", "پورتفولیو", CATEGORY_LABELS_EN["portfolio"], "work"),
    OrderTopic("education", "آموزش و وبینار", CATEGORY_LABELS_EN["education"], "assessment"),
    OrderTopic("jewelry", "طلا و جواهر", CATEGORY_LABELS_EN["jewelry"], "work", service_slug="ecommerce-platform"),
    OrderTopic("crm", "CRM سازمانی", "Enterprise CRM", "customers", "crm_orders:create", "custom-web-application"),
    OrderTopic("other", "ایده‌ای دیگر", "Another idea", "message", service_slug="custom-web-application"),
)
TOPIC_BY_KEY = {topic.key: topic for topic in TOPICS}
ADDONS = (("webapp", "سامانه یا پنل اختصاصی", "Custom application or portal"),
          ("support", "پشتیبانی و توسعه", "Support and development"))
CONSULTATION = ("مطمئن نیستم؛ اول مشاوره رایگان", "Not sure? Start with a free consultation")
CRM_MODULE_KEYS = ("customers", "sales", "visits", "correspondence", "support", "accounting", "inventory", "automation", "security")
CRM_ROADMAP_KEYS = ("ai", "accounting", "channels", "workflows", "mobile", "portal")


def crm_choices(lang):
    # Reuse the actual product catalogue; delayed import avoids a view cycle.
    from core.views.base import CRMProductView
    offset = 0 if lang == "fa" else 1
    return (tuple((key, row[offset]) for key, row in zip(CRM_MODULE_KEYS, CRMProductView.features)),
            tuple((key, row[offset]) for key, row in zip(CRM_ROADMAP_KEYS, CRMProductView.roadmap)))


def parse_choices(query):
    """Discard unknown keys/values; never pass through arbitrary query text."""
    topic = query.get("type", "")
    result = {"type": topic} if topic in TOPIC_BY_KEY else {}
    for key, allowed in (("addons", {row[0] for row in ADDONS}),
                         ("modules", set(CRM_MODULE_KEYS) if topic == "crm" else set()),
                         ("extensions", set(CRM_ROADMAP_KEYS) if topic == "crm" else set())):
        values = query.getlist(key) if hasattr(query, "getlist") else [query.get(key, "")]
        values = [part for value in values for part in value.split(",")]
        selected = sorted(set(values) & allowed)
        if selected:
            result[key] = ",".join(selected)
    if query.get("consult") == "1":
        result["consult"] = "1"
    for key, options in COMMON.items():
        value = query.get("brief_" + key, "")
        if value in {row[0] for row in options}:
            result["brief_" + key] = value
    goals = GOALS.get(topic, GOALS["corporate"] if topic == "other" else ())
    if query.get("brief_goal") in {row[0] for row in goals}:
        result["brief_goal"] = query["brief_goal"]
    return result


def request_type(choices):
    if choices.get("consult") == "1":
        return "consultation"
    addons = choices.get("addons", "").split(",")
    if "webapp" in addons:
        return "webapp"
    topic = choices.get("type")
    if topic in {"ecommerce", "jewelry"}:
        return "ecommerce"
    if topic:
        return "webapp" if topic in {"crm", "other"} else "website"
    return "support" if "support" in addons else "consultation"


def start_url(topic="", **choices):
    query = parse_choices({"type": topic, **choices})
    return reverse("project_start") + ("?" + urlencode(query) if query else "")


def topic_cards(lang):
    cards = []
    for topic in TOPICS:
        features = (demo_config_labels(lang, topic.key)["features"]
                    if topic.key in CATEGORY_FEATURE_KEYS else
                    crm_choices(lang)[0] if topic.key == "crm" else ())
        cards.append({"key": topic.key, "title": getattr(topic, "title_" + lang),
                      "icon": topic.icon, "features": [label for _, label in features[:3]],
                      "feature_keys": CATEGORY_FEATURE_KEYS.get(topic.key, ()),
                      "url": start_url(topic.key), "form_name": topic.form_name,
                      "specialist_fa": topic.key in {"crm", "clinic"}})
    return cards
