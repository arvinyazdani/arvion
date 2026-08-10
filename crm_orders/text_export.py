from django.utils import timezone

from .forms import CrmOrderForm


SECTIONS = (
    ("پیگیری سفارش", ("tracking_code", "status", "created_at", "privacy_accepted_at", "internal_notes")),
    ("سازمان و اطلاعات تماس", ("organization_name", "industry", "organization_size", "website", "contact_name", "job_title", "work_email", "phone")),
    ("نیاز کسب‌وکار", ("primary_goals", "departments", "customer_types", "lead_sources", "crm_user_count", "current_data_sources", "current_tools", "current_process", "main_pain_points", "success_metrics")),
    ("دامنه و قابلیت‌های CRM", ("required_capabilities", "customer_data_fields", "assignment_model", "reminder_types", "notification_channels", "critical_workflows", "correspondence_features", "ai_use_cases", "reporting_priorities", "reports_needed", "system_roles", "permission_requirements")),
    ("داده، فناوری و امنیت", ("devices", "mobile_requirement", "integration_types", "required_integrations", "migration_types", "migration_sources", "approximate_record_count", "hosting_preference", "audit_requirement", "security_requirements")),
    ("تصمیم و اجرای پروژه", ("delivery_strategy", "requested_services", "budget_range", "expected_timeline", "decision_process", "additional_notes")),
)

EXTRA_LABELS = {
    "tracking_code": "کد پیگیری", "status": "وضعیت", "created_at": "زمان ثبت",
    "privacy_accepted_at": "زمان پذیرش حریم خصوصی", "internal_notes": "یادداشت داخلی",
    "customer_data_fields": "داده‌های ضروری پرونده مشتری", "reminder_types": "موارد نیازمند یادآوری",
    "reporting_priorities": "گزارش‌های اولویت‌دار", "system_roles": "نقش‌های اصلی سامانه",
    "devices": "دستگاه‌های مورد استفاده",
}

EXTRA_CHOICES = {
    "customer_data_fields": {"identity": "اطلاعات هویتی", "contact": "اطلاعات تماس", "source": "منبع جذب", "interactions": "تعاملات و پیگیری‌ها", "contracts": "قراردادها و اسناد"},
    "reminder_types": {"call": "تماس", "meeting": "جلسه", "followup": "پیگیری", "contract": "قرارداد", "payment": "پرداخت", "ticket": "تیکت"},
    "reporting_priorities": {"sales": "فروش", "customers": "مشتریان", "service": "خدمات", "performance": "عملکرد", "finance": "مالی"},
    "system_roles": {"executive": "مدیر ارشد", "sales_manager": "مدیر فروش", "sales": "کارشناس فروش", "support": "پشتیبانی", "finance": "مالی", "admin": "مدیر سامانه"},
    "devices": {"desktop": "رایانه", "mobile": "موبایل", "tablet": "تبلت"},
}


def _choice_map(form, order, field_name):
    form_choices = getattr(form.fields.get(field_name), "choices", ())
    if form_choices:
        return dict(form_choices)
    model_field = order._meta.get_field(field_name)
    if model_field.choices:
        return dict(model_field.flatchoices)
    return EXTRA_CHOICES.get(field_name, {})


def _display_value(form, order, field_name):
    value = getattr(order, field_name)
    if value in (None, "", []):
        return "—"
    if hasattr(value, "isoformat"):
        if hasattr(value, "hour"):
            value = timezone.localtime(value)
            return value.strftime("%Y-%m-%d %H:%M")
        return value.isoformat()
    choices = _choice_map(form, order, field_name)
    if isinstance(value, list):
        return "، ".join(str(choices.get(item, item)) for item in value) or "—"
    return str(choices.get(value, value))


def render_crm_order_text(order):
    form = CrmOrderForm(instance=order)
    lines = ["گزارش کامل نیازسنجی CRM آرویون", "=" * 42, f"سازمان: {order.organization_name}", f"کد پیگیری: {order.tracking_code}", ""]
    for section_title, field_names in SECTIONS:
        lines.extend((section_title, "-" * len(section_title)))
        for field_name in field_names:
            label = form.fields[field_name].label if field_name in form.fields else EXTRA_LABELS.get(field_name, field_name)
            lines.append(f"{label}: {_display_value(form, order, field_name)}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"
