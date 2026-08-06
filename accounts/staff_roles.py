"""Least-privilege staff roles used by the Rvion operations team."""

STAFF_ROLES = {
    "sales": {
        "label_fa": "فروش و درخواست‌ها",
        "permissions": {
            "leads.lead": {"view", "change"},
            "services.service": {"view"},
        },
    },
    "assessments": {
        "label_fa": "عملیات و محتوای آزمون",
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
        },
    },
    "support": {
        "label_fa": "پشتیبانی مشتریان",
        "permissions": {
            "assessments.supportticket": {"view", "change"},
            "assessments.order": {"view"},
            "assessments.attemptresult": {"view"},
            "assessments.certificate": {"view"},
        },
    },
    "content": {
        "label_fa": "محتوا و وب‌سایت",
        "permissions": {
            "blog.post": {"view", "add", "change"},
            "projects.project": {"view", "add", "change"},
            "services.service": {"view", "add", "change"},
            "core.page": {"view", "add", "change"},
        },
    },
}


def group_name(role):
    return f"rvion_{role}"
