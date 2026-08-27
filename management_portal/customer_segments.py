from datetime import timedelta

from django.db.models import Q
from django.utils import timezone


ALLOWED_SEGMENT_FILTERS = {"q", "journey", "case_stage", "inactive_days"}
JOURNEY_CHOICES = (
    ("registered", "عضو بدون سفارش", "Registered without order"),
    ("unpaid", "سفارش پرداخت‌نشده", "Unpaid order"),
    ("payment_review", "پرداخت منتظر بررسی", "Payment awaiting review"),
    ("ready", "پرداخت‌شده و شروع‌نشده", "Paid, not started"),
    ("completed", "نتیجه آماده", "Result ready"),
)


def normalize_segment_filters(values):
    filters = {key: str(values.get(key, "")).strip() for key in ALLOWED_SEGMENT_FILTERS}
    if filters["journey"] not in {item[0] for item in JOURNEY_CHOICES}:
        filters["journey"] = ""
    if filters["case_stage"] not in {"new", "discovery", "qualified", "proposal", "won", "lost"}:
        filters["case_stage"] = ""
    try:
        days = int(filters["inactive_days"] or 0)
    except (TypeError, ValueError):
        days = 0
    filters["inactive_days"] = str(min(max(days, 0), 365)) if days else ""
    return {key: value for key, value in filters.items() if value}


def apply_customer_filters(queryset, filters):
    query = filters.get("q", "")
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) | Q(phone__icontains=query) | Q(email__icontains=query)
            | Q(contacts__name__icontains=query) | Q(contacts__phone__icontains=query)
            | Q(contacts__email__icontains=query)
        )
    stage = filters.get("case_stage")
    if stage:
        queryset = queryset.filter(cases__stage=stage)
    if filters.get("inactive_days"):
        cutoff = timezone.now() - timedelta(days=int(filters["inactive_days"]))
        queryset = queryset.filter(updated_at__lt=cutoff).exclude(events__occurred_at__gte=cutoff)
    journey = filters.get("journey")
    if journey == "registered":
        queryset = queryset.filter(contacts__user__is_active=True).exclude(assessment_orders__isnull=False)
    elif journey == "unpaid":
        queryset = queryset.filter(assessment_orders__status="pending").exclude(assessment_orders__manual_payment__status="pending")
    elif journey == "payment_review":
        queryset = queryset.filter(assessment_orders__manual_payment__status="pending")
    elif journey == "ready":
        queryset = queryset.filter(assessment_orders__status="paid").exclude(assessment_orders__user__exam_attempts__isnull=False)
    elif journey == "completed":
        queryset = queryset.filter(assessment_orders__user__exam_attempts__status="completed")
    return queryset.distinct()
