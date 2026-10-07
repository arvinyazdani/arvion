from django.conf import settings
from django.middleware.csrf import get_token
from django.db.models import Q
from django.utils import timezone
from django.urls import reverse
from .inbox import safe_inbox_return


def _management_navigation(request, lang):
    """Match navigation to existing view permissions, not a new access policy."""
    user = request.user
    current = getattr(request.resolver_match, "url_name", "")
    english = lang == "en"

    def item(route, fa, en, icon, names):
        return {"url": reverse("management_portal:" + route),
                "label": en if english else fa, "icon": icon,
                "active": current in names}

    today = item("dashboard", "امروز", "Today", "home", {"dashboard"})
    customers = item("customer_workspace", "مشتریان", "Customers", "customers", {
        "customer_workspace", "customer_detail", "customer_duplicates",
        "customer_assessment_detail", "crm_workspace", "crm_case_detail",
    })
    operational = []
    if user.has_perm("assessments.view_exam") or user.has_perm("assessments.view_supportticket"):
        operational.append(item("assessment_support", "آزمون‌ها", "Assessments", "assessment", {"assessment_support"}))
    if user.has_perm("assessments.view_manualpaymentsubmission") or user.has_perm("accounts.change_user"):
        operational.append(item("approvals", "پرداخت و تأیید" if user.has_perm("assessments.view_manualpaymentsubmission") else "تأیید حساب",
                                "Approvals", "check", {"approvals"}))
    projects = []
    if any(user.has_perm(perm) for perm in ("leads.view_lead", "crm_orders.view_crmorder", "clinic_orders.view_clinicorder")):
        projects.append(item("request_list", "درخواست و نیازسنجی", "Enquiries", "forms", {"request_list", "request_detail"}))
    # Workspace views already allow all staff; do not introduce a new role rule.
    projects.append(item("workspace_list", "سفارش و قرارداد", "Orders & contracts", "contract", {
        "workspace_list", "workspace_detail", "workspace_questionnaire", "workspace_general_terms",
        "contract_list", "contract_create", "contract_detail", "contract_edit",
        "contract_preview", "contract_clauses", "contract_settings",
    }))
    desktop = [today, customers, *operational, *projects]
    mobile_labels = {
        "assessment": ("آزمون‌ها", "Exams"),
        "check": ("پرداخت‌ها" if user.has_perm("assessments.view_manualpaymentsubmission") else "تأییدها", "Approvals"),
        "forms": ("درخواست‌ها", "Enquiries"),
        "contract": ("قراردادها", "Contracts"),
    }
    mobile = [dict(entry) for entry in [today, customers, *(operational + projects)[:2]]]
    for entry in mobile:
        if entry["icon"] in mobile_labels:
            entry["label"] = mobile_labels[entry["icon"]][int(english)]
    return {
        "management_primary_nav": desktop,
        "management_mobile_nav": mobile,
        "management_more_desktop_active": not any(entry["active"] for entry in desktop),
        "management_more_mobile_active": not any(entry["active"] for entry in mobile),
        "management_search_query": request.GET.get("q", "") if current == "customer_workspace" else "",
    }


def management_alerts(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated or not request.user.is_staff:
        return {}
    get_token(request)  # Push subscription POST must work even on read-only dashboard pages.
    current_lang = getattr(request, "LANGUAGE_CODE", "fa")
    other_lang = "en" if current_lang == "fa" else "fa"
    path_parts = request.path.split("/")
    if len(path_parts) > 1 and path_parts[1] in {"fa", "en"}:
        path_parts[1] = other_lang
    language_switch_url = "/".join(path_parts)
    if request.META.get("QUERY_STRING"):
        language_switch_url += "?" + request.META["QUERY_STRING"]
    unread_count = getattr(request, "_management_unread_count", None)
    if unread_count is None:
        unread_count = request.user.notification_receipts.filter(
            seen_at__isnull=True,
            dismissed_at__isnull=True,
            notification__status__in=("unread", "read"),
        ).filter(
            Q(snoozed_until__isnull=True) | Q(snoozed_until__lte=timezone.now()),
        ).count()
    return {
        **_management_navigation(request, current_lang),
        "web_push_public_key": settings.WEB_PUSH_VAPID_PUBLIC_KEY,
        "unread_count": unread_count,
        "language_switch_url": language_switch_url,
        "inbox_return_url": safe_inbox_return(request.GET.get("inbox_return")),
    }
