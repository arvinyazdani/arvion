"""Read-only presentation of assessment state and financial evidence."""
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse

from assessments.models import Attempt, Exam, ManualPaymentSubmission, Order
from .models import CustomerContact, OperationalAudit


ATTEMPT_LABELS = {
    "ready": ("آماده", "Ready"), "in_progress": ("در حال انجام", "In progress"),
    "submitted": ("ارسال‌شده", "Submitted"), "expired": ("منقضی‌شده", "Expired"),
    "scoring": ("در حال ارزیابی", "Scoring"), "completed": ("تکمیل‌شده", "Completed"),
    "invalidated": ("باطل‌شده", "Invalidated"),
}
PAYMENT_LABELS = {"pending": ("منتظر بررسی", "Awaiting review"), "approved": ("تأییدشده", "Approved"), "rejected": ("ردشده", "Rejected")}


def label(pair, lang):
    return pair[0 if lang == "fa" else 1]


def review_page(rows, request, key="page", anchor=""):
    page = Paginator(rows, 20).get_page(request.GET.get(key))
    query = request.GET.copy()
    query.pop(key, None)
    page.previous_url = page.next_url = ""
    for attr, available, number in (
        ("previous_url", page.has_previous(), page.number - 1),
        ("next_url", page.has_next(), page.number + 1),
    ):
        if available:
            query[key] = number
            setattr(page, attr, "?" + query.urlencode() + ("#" + anchor if anchor else ""))
    return page


def order_evidence(order, lang):
    """Describe known provenance only; paid/zero amount alone is not bank proof.

    Transactions must be prefetched. Never serialize their raw provider payload.
    """
    verified = [t for t in order.transactions.all() if t.status == "verified"]
    receipt = getattr(order, "manual_payment", None)
    source = ("منبع دسترسی مشخص نیست", "Access source not recorded")
    if order.gateway == "welcome_trial" and order.amount_irr == 0:
        source = ("هدیه ثبت‌نام · بدون دریافت وجه", "Welcome gift · no money collected")
    elif verified and order.amount_irr == 0:
        source = ("دسترسی بدون هزینه · بدون دریافت وجه", "No-cost access · no money collected")
    elif receipt and receipt.status == "approved":
        flags = [t.raw_response for t in verified if isinstance(t.raw_response, dict)]
        if any(f.get("automatic_review") is True for f in flags):
            source = ("تأیید خودکار سیستم · نیازمند تطبیق بانکی", "Automatic approval · bank reconciliation required")
        elif receipt.reviewed_by_id:
            source = ("رسید تأییدشده توسط مدیر", "Receipt approved by a manager")
        else:
            source = ("رسید تأییدشده · روش بررسی ثبت نشده", "Approved receipt · review method not recorded")
    elif verified and order.gateway not in {"sandbox", "benchmark", "test", "card_transfer"}:
        source = ("تراکنش تأییدشده درگاه", "Verified gateway transaction")
    elif verified and order.gateway == "sandbox":
        source = ("دسترسی آزمایشی · پرداخت بانکی نیست", "Sandbox access · not a bank payment")
    elif receipt and receipt.status == "pending":
        source = ("رسید ارسال‌شده · هنوز بررسی نشده", "Receipt submitted · not yet reviewed")
    elif receipt and receipt.status == "rejected":
        source = ("رسید ردشده", "Rejected receipt")
    entitlement = getattr(order, "entitlement", None)
    if entitlement and entitlement.is_revoked:
        access = ("دسترسی بسته‌شده", "Access closed")
    elif entitlement:
        access = ("دسترسی صادر شده", "Access issued")
    else:
        access = ("دسترسی صادر نشده", "Access not issued")
    return {"source": label(source, lang), "access": label(access, lang), "receipt": receipt,
            "amount": f"{order.amount_irr:,}", "subtotal": f"{order.subtotal_irr:,}", "discount": f"{order.discount_irr:,}"}


def assessment_list(request):
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    status = request.GET.get("status", "")
    status = status if status in ATTEMPT_LABELS else ""
    q = request.GET.get("q", "").strip()[:150]
    exam_id = request.GET.get("exam", "")
    exam_id = int(exam_id) if exam_id.isascii() and exam_id.isdigit() and len(exam_id) <= 18 else None
    rows = Attempt.objects.select_related("user", "exam", "result").order_by("-created_at", "-pk")
    if status:
        rows = rows.filter(status=status)
    if q:
        rows = rows.filter(Q(user__email__icontains=q) | Q(user__mobile__icontains=q) | Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q))
    if exam_id:
        rows = rows.filter(exam_id=exam_id)
    page = review_page(rows, request, "attempts_page", "attempt-list")
    for attempt in page:
        attempt.management_status = label(ATTEMPT_LABELS[attempt.status], lang)
        attempt.review_url = reverse("management_portal:assessment_attempt_detail", args=[attempt.pk])
    return {"attempts": page, "attempt_page": page, "q": q, "attempt_status": status,
            "exam_filter": exam_id, "attempt_statuses": [(key, label(pair, lang)) for key, pair in ATTEMPT_LABELS.items()],
            "exams": Exam.objects.all().order_by("pk")}


def payment_list(request, payment_pk):
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    status = request.GET.get("payment_status", "")
    status = status if status in PAYMENT_LABELS else ""
    q = request.GET.get("q", "").strip()[:150]
    rows = ManualPaymentSubmission.objects.select_related(
        "order__user", "order__customer", "order__exam", "order__entitlement", "reviewed_by",
    ).prefetch_related("order__transactions").order_by("-created_at", "-pk")
    if payment_pk is not None:
        rows = rows.filter(pk=payment_pk)
    else:
        if status:
            rows = rows.filter(status=status)
        if q:
            rows = rows.filter(Q(reference_number__icontains=q) | Q(payer_name__icontains=q) | Q(order__user__email__icontains=q) | Q(order__user__mobile__icontains=q))
    page = review_page(rows, request, "payments_page", "payment-list")
    customers = {}
    for account_id, customer_id in CustomerContact.objects.filter(user_id__in=[p.order.user_id for p in page]).order_by("pk").values_list("user_id", "customer_id"):
        customers.setdefault(account_id, customer_id)
    for payment in page:
        payment.evidence = order_evidence(payment.order, lang)
        customer_id = payment.order.customer_id or customers.get(payment.order.user_id)
        payment.customer_url = reverse("management_portal:customer_detail", args=[customer_id]) if customer_id else ""
        payment.report_url = reverse("management_portal:customer_assessment_detail", args=[customer_id, payment.order.user_id]) + f"?order={payment.order_id}#order-{payment.order_id}" if customer_id else ""
        payment.history = []
        payment.history_count = 0
        if payment_pk is not None:
            history = OperationalAudit.objects.filter(
                Q(target_type="manual_payment", target_id=str(payment.pk)) |
                Q(target_type="assessment_order", target_id=str(payment.order_id)),
            ).select_related("actor").order_by("-created_at", "-pk")
            payment.history_count = history.count()
            payment.history = list(history[:20])
            actions = {"payment_approve": ("تأیید رسید", "Receipt approved"), "payment_reject": ("رد رسید", "Receipt rejected"),
                       "notification_payment_approve": ("تأیید رسید از صندوق کار", "Receipt approved from work inbox"),
                       "notification_payment_reject": ("رد رسید از صندوق کار", "Receipt rejected from work inbox"),
                       "assessment_access_revoked": ("بستن دسترسی آزمون", "Assessment access closed")}
            for event in payment.history:
                event.review_label = label(actions.get(event.action, ("عملیات ثبت‌شده", "Recorded action")), lang)
    return {"payments": page, "payment_page": page, "payment_status": status, "payment_query": q,
            "payment_selected": payment_pk is not None,
            "payment_statuses": [(key, label(pair, lang)) for key, pair in PAYMENT_LABELS.items()]}
