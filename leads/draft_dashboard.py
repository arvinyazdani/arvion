"""Builds the small, safe view model `accounts.views.dashboard` renders
for a customer's own in-progress `leads_contact` FormDraft (V2.1-C2).

`build_draft_dashboard_card` is the only function here; it takes the
`FormDraft` instance already returned by `leads.form_draft_service.
get_active_draft` (read-only, owner-scoped, excludes expired/submitted)
and returns either `None` or a `DraftDashboardCard` — a plain, frozen
dataclass carrying only the values this phase's design explicitly
allowlists for display: current step, progress, last-saved/expiry
timestamps, the four allowlisted choice fields (translated to both
languages), the selected service's title if any, and — from the frozen
`demo_snapshot` only, never a live `DemoSelection` — the demo's bilingual
template title and category. `demo_snapshot["brand"]` is deliberately
never read here (V2.1-C2 corrective): it is the one snapshot field that
is not bilingual — a single free-text-ish value that may fall back to
the template's Persian `fictional_brand_fa` regardless of which language
is rendering — so showing it in either language on this card would leak
the wrong language's text. `template_title_*`/`category_*` remain fully
bilingual and are the only demo fields this card shows. It never exposes
`submission_token`, the draft's own id, the owner's id, `revision`, or
any forbidden (contact/free-text) field, and it never writes to the
database or mutates the draft.

The choice labels below intentionally mirror `leads.forms.lead_form.
LeadForm`'s own Persian labels and `leads.models.Lead`'s English choice
text verbatim, kept as a separate, display-only copy here rather than
importing/refactoring the form: this phase changes only read-only
dashboard display, never the submission form or its validation.
"""

from dataclasses import dataclass
from typing import Optional

from django.utils import timezone

from services.models import Service

from .form_draft_service import FORM_TYPE_STEP_COUNTS

_REQUEST_TYPE_LABELS = {
    "consultation": ("مشاوره اولیه", "Consultation"),
    "website": ("وب‌سایت شرکتی", "Website"),
    "webapp": ("وب‌اپلیکیشن اختصاصی", "Web application"),
    "ecommerce": ("فروشگاه و تجارت آنلاین", "E-commerce"),
    "support": ("پشتیبانی و بهینه‌سازی", "Support and optimization"),
    "training": ("آموزش", "Training Request"),
    "other": ("سایر", "Other"),
}
_BUDGET_RANGE_LABELS = {
    "unsure": ("هنوز مطمئن نیستم", "Not sure yet"),
    "under_50": ("کمتر از ۵۰ میلیون تومان", "Under 50 million toman"),
    "50_150": ("۵۰ تا ۱۵۰ میلیون تومان", "50–150 million toman"),
    "150_500": ("۱۵۰ تا ۵۰۰ میلیون تومان", "150–500 million toman"),
    "over_500": ("بیش از ۵۰۰ میلیون تومان", "Over 500 million toman"),
}
_TIMELINE_LABELS = {
    "flexible": ("زمان‌بندی منعطف", "Flexible"),
    "one_month": ("کمتر از یک ماه", "Within one month"),
    "one_three": ("یک تا سه ماه", "One to three months"),
    "over_three": ("بیش از سه ماه", "More than three months"),
}
_CONTACT_METHOD_LABELS = {
    "phone": ("تماس تلفنی", "Phone"),
    "email": ("ایمیل", "Email"),
    "telegram": ("تلگرام", "Telegram"),
}

_DEMO_SNAPSHOT_REQUIRED_KEYS = ("template_title_fa", "template_title_en", "category_fa", "category_en")


@dataclass(frozen=True)
class DraftDemoSummary:
    title_fa: str
    title_en: str
    category_fa: str
    category_en: str


@dataclass(frozen=True)
class DraftDashboardCard:
    current_step: int
    total_steps: int
    progress_percent: int
    updated_at: "object"
    expires_at: "object"
    days_remaining: int
    request_type_label_fa: Optional[str]
    request_type_label_en: Optional[str]
    budget_range_label_fa: Optional[str]
    budget_range_label_en: Optional[str]
    timeline_label_fa: Optional[str]
    timeline_label_en: Optional[str]
    preferred_contact_label_fa: Optional[str]
    preferred_contact_label_en: Optional[str]
    service_title_fa: Optional[str]
    service_title_en: Optional[str]
    demo: Optional[DraftDemoSummary]


def _label_pair(value, labels):
    pair = labels.get(value) if isinstance(value, str) else None
    return pair if pair is not None else (None, None)


def _service_titles(fields):
    service_id = fields.get("service_id")
    if not isinstance(service_id, int) or isinstance(service_id, bool):
        return None, None
    service = Service.objects.filter(pk=service_id).first()
    if service is None:
        return None, None
    return service.title_fa, service.title_en


def _demo_summary(demo_snapshot):
    if not isinstance(demo_snapshot, dict) or not demo_snapshot:
        return None
    if not all(key in demo_snapshot for key in _DEMO_SNAPSHOT_REQUIRED_KEYS):
        return None
    values = {key: demo_snapshot.get(key) for key in _DEMO_SNAPSHOT_REQUIRED_KEYS}
    if not all(isinstance(value, str) and value for value in values.values()):
        return None
    return DraftDemoSummary(
        title_fa=values["template_title_fa"], title_en=values["template_title_en"],
        category_fa=values["category_fa"], category_en=values["category_en"],
    )


def build_draft_dashboard_card(draft):
    """`draft` must be the result of `get_active_draft` (or `None`) —
    never a raw, unfiltered `FormDraft` lookup. Returns `None` for `None`
    input; otherwise always returns a card, even from an empty or
    malformed `fields`/`demo_snapshot` (never raises)."""
    if draft is None:
        return None

    fields = draft.fields if isinstance(draft.fields, dict) else {}
    total_steps = FORM_TYPE_STEP_COUNTS.get(draft.form_type, 1)
    raw_step = draft.current_step if isinstance(draft.current_step, int) else 0
    current_step = min(max(raw_step, 0), total_steps - 1) + 1
    progress_percent = round((current_step / total_steps) * 100)
    days_remaining = max(0, (draft.expires_at - timezone.now()).days)

    request_type_fa, request_type_en = _label_pair(fields.get("request_type"), _REQUEST_TYPE_LABELS)
    budget_range_fa, budget_range_en = _label_pair(fields.get("budget_range"), _BUDGET_RANGE_LABELS)
    timeline_fa, timeline_en = _label_pair(fields.get("timeline"), _TIMELINE_LABELS)
    preferred_contact_fa, preferred_contact_en = _label_pair(fields.get("preferred_contact"), _CONTACT_METHOD_LABELS)
    service_title_fa, service_title_en = _service_titles(fields)

    return DraftDashboardCard(
        current_step=current_step, total_steps=total_steps, progress_percent=progress_percent,
        updated_at=draft.updated_at, expires_at=draft.expires_at, days_remaining=days_remaining,
        request_type_label_fa=request_type_fa, request_type_label_en=request_type_en,
        budget_range_label_fa=budget_range_fa, budget_range_label_en=budget_range_en,
        timeline_label_fa=timeline_fa, timeline_label_en=timeline_en,
        preferred_contact_label_fa=preferred_contact_fa, preferred_contact_label_en=preferred_contact_en,
        service_title_fa=service_title_fa, service_title_en=service_title_en,
        demo=_demo_summary(draft.demo_snapshot),
    )
