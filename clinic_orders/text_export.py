from django.utils import timezone
from .forms import ClinicOrderForm


SECTIONS = (
    ("پیگیری", ("tracking_code", "status", "created_at", "privacy_accepted_at", "internal_notes")),
    ("کلینیک و تماس", ("clinic_name", "clinic_type", "city", "branch_count", "specialties", "practitioner_count", "website", "contact_name", "job_title", "work_email", "phone")),
    ("هدف و فرآیند", ("primary_goals", "target_audiences", "current_channels", "current_process", "main_pain_points", "success_metrics")),
    ("نوبت‌دهی، حساب و پرداخت", ("visit_modes", "schedule_model", "appointment_rules", "intake_requirements", "reminder_channels", "waitlist_requirement", "practitioner_features", "patient_account_features", "payment_methods", "pricing_model", "insurance_requirement", "cancellation_refund_rules", "financial_documents")),
    ("محتوا و وبینار", ("content_types", "content_access", "publishing_workflow", "media_requirements", "webinar_features", "webinar_platform", "expected_live_attendees")),
    ("فناوری، امنیت و اجرا", ("system_roles", "record_scope", "notification_channels", "integration_types", "required_integrations", "migration_sources", "security_requirements", "hosting_preference", "delivery_strategy", "requested_services", "budget_range", "expected_timeline", "decision_process", "additional_notes")),
)
EXTRA_LABELS = {"tracking_code": "کد پیگیری", "status": "وضعیت", "created_at": "زمان ثبت", "privacy_accepted_at": "پذیرش حریم خصوصی", "internal_notes": "یادداشت داخلی"}


def _display(form, order, name):
    value = getattr(order, name)
    if value in (None, "", []):
        return "—"
    if hasattr(value, "isoformat"):
        return timezone.localtime(value).strftime("%Y-%m-%d %H:%M") if hasattr(value, "hour") else value.isoformat()
    choices = dict(getattr(form.fields.get(name), "choices", ()) or order._meta.get_field(name).flatchoices)
    if isinstance(value, list):
        return "، ".join(str(choices.get(item, item)) for item in value)
    return str(choices.get(value, value))


def render_clinic_order_text(order):
    form = ClinicOrderForm(instance=order)
    lines = ["گزارش کامل نیازسنجی وب‌سایت کلینیک آرویون", "=" * 48, f"کلینیک: {order.clinic_name}", f"کد پیگیری: {order.tracking_code}", ""]
    for title, names in SECTIONS:
        lines.extend((title, "-" * len(title)))
        for name in names:
            label = form.fields[name].label if name in form.fields else EXTRA_LABELS.get(name, name)
            lines.append(f"{label}: {_display(form, order, name)}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"
