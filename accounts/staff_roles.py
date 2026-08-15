"""Least-privilege staff roles used by the Rvion operations team."""

STAFF_ROLES = {
    "sales": {
        "label_fa": "فروش و درخواست‌ها",
        "label_en": "Sales & requests",
        "permissions": {
            "leads.lead": {"view", "change"},
            "crm_orders.crmorder": {"view", "change"},
            "clinic_orders.clinicorder": {"view", "change"},
            "services.service": {"view"},
        },
    },
    "assessments": {
        "label_fa": "عملیات و محتوای آزمون",
        "label_en": "Assessment operations & content",
        "permissions": {
            "assessments.exam": {"view", "add", "change"},
            "assessments.examversion": {"view", "add", "change"},
            "assessments.examsection": {"view", "add", "change"},
            "assessments.question": {"view", "add", "change"},
            "assessments.choice": {"view", "add", "change"},
            "assessments.skill": {"view", "add", "change"},
            "assessments.attempt": {"view"},
            "assessments.attemptresult": {"view"},
            "assessments.skillresult": {"view"},
            "assessments.integrityevent": {"view"},
            "assessments.certificate": {"view", "change"},
            "assessments.examentitlement": {"view"},
            "assessments.order": {"view"},
            "assessments.paymenttransaction": {"view"},
            "assessments.manualpaymentsubmission": {"view", "change"},
        },
    },
    "support": {
        "label_fa": "پشتیبانی مشتریان",
        "label_en": "Customer support",
        "permissions": {
            "assessments.supportticket": {"view", "change"},
            "assessments.order": {"view"},
            "assessments.attemptresult": {"view"},
            "assessments.certificate": {"view"},
        },
    },
    "content": {
        "label_fa": "محتوا و وب‌سایت",
        "label_en": "Content & website",
        "permissions": {
            "blog.post": {"view", "add", "change"},
            "projects.project": {"view", "add", "change"},
            "services.service": {"view", "add", "change"},
            "core.page": {"view", "add", "change"},
        },
    },
    "analytics": {
        "label_fa": "گزارش بازدید",
        "label_en": "Traffic analytics",
        "permissions": {
            "traffic.trafficday": {"view"},
            "traffic.activevisitor": {"view"},
        },
    },
}


def group_name(role):
    return f"rvion_{role}"


def sync_staff_role_groups():
    """Create/update the fixed least-privilege groups and return them by role."""
    from django.contrib.auth.models import Group, Permission
    from django.core.exceptions import ImproperlyConfigured

    groups = {}
    for role, config in STAFF_ROLES.items():
        group, _ = Group.objects.get_or_create(name=group_name(role))
        permissions = []
        for model_key, actions in config["permissions"].items():
            app_label, model = model_key.split(".")
            for action in actions:
                try:
                    permissions.append(Permission.objects.get(
                        content_type__app_label=app_label,
                        content_type__model=model,
                        codename=f"{action}_{model}",
                    ))
                except Permission.DoesNotExist as exc:
                    raise ImproperlyConfigured(f"Missing permission: {app_label}.{action}_{model}") from exc
        group.permissions.set(permissions)
        groups[role] = group
    return groups
