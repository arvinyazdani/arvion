"""Read-only, permission-scoped summaries. Counts are never preview lengths."""
from datetime import timedelta

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Exists, OuterRef, Q
from django.urls import reverse

from accounts.models import User
from contracts.models import ContractProposal
from assessments.models import Attempt, Order, PaymentTransaction
from .models import CaseTask


def prepare_today(user, now, lang, queue, metrics, selected_group="", page="1"):
    en = lang == "en"
    label = lambda fa, english: english if en else fa
    sales = any(user.has_perm(p) for p in (
        "leads.view_lead", "crm_orders.view_crmorder", "clinic_orders.view_clinicorder"))
    tasks = CaseTask.objects.none()
    contract_count = 0
    if user.is_superuser:
        contracts = ContractProposal.objects.filter(status__in=("sent", "review"), created_at__lte=now-timedelta(seconds=settings.SALES_FOLLOW_UP_SLA_SECONDS)).order_by("created_at", "pk")
        contract_count = contracts.count()
        for contract in contracts[:8]:
            queue.append({"kind": label("قرارداد", "Contract"), "title": contract.customer_name,
                          "meta": contract.project_title, "date": contract.created_at,
                          "url": reverse("management_portal:workspace_detail", args=[contract.customer_case_id]) if contract.customer_case_id else reverse("contracts:proposal_detail", args=[contract.pk])})
    if sales:
        tasks = CaseTask.objects.filter(status="open").select_related("case").order_by("due_at", "pk")
        for task in tasks.filter(due_at__lte=now)[:8]:
            queue.append({"kind": label("وظیفه", "Task"), "title": task.title,
                          "meta": task.case.customer_name, "date": task.due_at,
                          "url": reverse("management_portal:crm_case_detail", args=[task.case_id])})
    payment = label("پرداخت", "Payment")
    support = label("پشتیبانی", "Support")
    task_kind = label("وظیفه", "Task")
    for item in queue:
        if item["kind"] == payment:
            item["rank"] = 0
        elif item["kind"] == task_kind or (
            item["kind"] == support and item.get("waiting_first_response") and item["date"] <= now - timedelta(seconds=settings.SUPPORT_FIRST_RESPONSE_SLA_SECONDS)
        ) or (item["kind"] in {"CRM", label("کلینیک", "Clinic"), label("همکاری", "Enquiry"), label("قرارداد", "Contract")} and item["date"] <= now - timedelta(seconds=settings.SALES_FOLLOW_UP_SLA_SECONDS)):
            item["rank"] = 1
        else:
            item["rank"] = 2
        item["priority"] = label("فوری", "Urgent") if item["rank"] == 0 else label("سررسید گذشته", "Overdue") if item["rank"] == 1 else label("در انتظار", "Waiting")
    queue.sort(key=lambda item: (item["rank"], item["date"], item["url"]))
    # Only metrics that represent actionable source rows contribute to work count.
    kinds = {"حساب نیازمند تأیید", "درخواست همکاری جدید", "نیازسنجی CRM", "نیازسنجی کلینیک", "پرداخت منتظر بررسی", "تیکت باز",
             "Accounts awaiting approval", "New enquiries", "CRM discoveries", "Clinic discoveries", "Payments awaiting review", "Open tickets"}
    work_count = sum(m["value"] for m in metrics if m["label"] in kinds) + tasks.filter(due_at__lte=now).count() + contract_count
    summaries = [dict(label=label("کار منتظر اقدام", "Work awaiting action"), value=work_count,
                      url="#work-queue-title", description=label("موارد، نه تعداد مشتری", "Items, not unique customers"), tone="warning")]
    for metric in metrics:
        if metric["label"] in {"اعلان خوانده‌نشده", "Unread alerts", "پرداخت منتظر بررسی", "Payments awaiting review", "آزمون در حال اجرا", "Active assessments"}:
            summaries.append(metric)
    for metric in metrics:
        if len(summaries) < 4 and metric["label"] in kinds and metric not in summaries:
            summaries.append(metric)
    groups = []
    def group(key, fa, english, qs, unit):
        selected = key == selected_group
        page_obj = Paginator(qs, 30).get_page(page) if selected else None
        groups.append({"key": key, "label": label(fa, english), "count": qs.count(),
                       "unit": unit, "selected": selected, "page": page_obj,
                       "items": list(page_obj) if selected else list(qs[:3])})
    if user.has_perm("accounts.change_user") or user.has_perm("assessments.view_exam"):
        group("registered", "عضو شده، بدون سفارش", "Registered, no order",
              User.objects.filter(is_staff=False, is_active=True, assessment_orders__isnull=True).order_by("-date_joined", "pk"), label("نفر", "people"))
    if user.has_perm("assessments.view_exam") or user.has_perm("assessments.view_manualpaymentsubmission"):
        orders = Order.objects.select_related("user", "exam", "customer", "manual_payment").annotate(
            has_verified_transaction=Exists(PaymentTransaction.objects.filter(order_id=OuterRef("pk"), status="verified")))
        group("pending", "سفارش داده، پرداخت نکرده", "Ordered, unpaid",
              orders.filter(status="pending").exclude(manual_payment__status="pending").order_by("created_at", "pk"), label("سفارش", "orders"))
        ready = orders.filter(status="paid", entitlement__isnull=False, entitlement__attempt__isnull=True,
                              entitlement__revoked_at__isnull=True, entitlement__attempts_remaining__gt=0).filter(
                                  Q(entitlement__expires_at__isnull=True) | Q(entitlement__expires_at__gt=now))
        group("ready", "دسترسی فعال، شروع‌نشده", "Active access, not started", ready.order_by("created_at", "pk"), label("دسترسی", "access grants"))
        for order in groups[-1]["items"]:
            if order.amount_irr == 0:
                order.access_label = label("رایگان / هدیه", "Free / gift")
            elif order.has_verified_transaction:
                order.access_label = label("پرداخت درگاه تأییدشده", "Verified gateway payment")
            elif getattr(order, "manual_payment", None) and order.manual_payment.status == "approved":
                order.access_label = label("رسید تأییدشده", "Approved receipt")
            else:
                order.access_label = label("دسترسی صادرشده؛ واریز تأیید نشده", "Access granted; transfer not verified")
    if user.has_perm("assessments.view_exam"):
        group("completed", "آزمون کامل شده", "Assessment completed",
              Attempt.objects.filter(status="completed").select_related("user", "exam", "entitlement__order__customer", "result").order_by("-submitted_at", "pk"), label("آزمون", "assessments"))
    return {"queues": queue[:8], "queue_total": work_count, "today_summaries": summaries[:4],
            "today_groups": groups}
