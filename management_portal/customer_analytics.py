from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from assessments.models import Attempt, Order

from .models import Customer, CustomerCase, CustomerEvent
from .customer_segments import CASE_STAGE_CHOICES


EVENT_CATEGORY_LABELS = {
    "identity": ("هویت و عضویت", "Identity"),
    "order": ("سفارش", "Order"),
    "payment": ("پرداخت", "Payment"),
    "assessment": ("آزمون", "Assessment"),
    "contract": ("قرارداد", "Contract"),
    "support": ("پشتیبانی", "Support"),
    "sales": ("فروش و پیگیری", "Sales & follow-up"),
}


def _percent(value, base):
    return round((value / base) * 100, 1) if base else 0


def build_customer_funnel():
    registered = Customer.objects.filter(contacts__user__is_active=True).distinct().count()
    ordered = Customer.objects.filter(assessment_orders__isnull=False).distinct().count()
    paid = Customer.objects.filter(assessment_orders__status="paid").distinct().count()
    started = Customer.objects.filter(assessment_orders__user__exam_attempts__started_at__isnull=False).distinct().count()
    completed = Customer.objects.filter(assessment_orders__user__exam_attempts__status="completed").distinct().count()
    raw = (
        ("registered", "عضویت فعال", "Active account", registered),
        ("ordered", "ثبت سفارش", "Order created", ordered),
        ("paid", "پرداخت موفق", "Payment approved", paid),
        ("started", "شروع آزمون", "Assessment started", started),
        ("completed", "نتیجه آماده", "Result ready", completed),
    )
    stages = []
    previous = registered
    for index, (key, label_fa, label_en, count) in enumerate(raw):
        stages.append({
            "key": key, "label_fa": label_fa, "label_en": label_en,
            "count": count, "share": _percent(count, registered),
            "step_conversion": 100 if index == 0 else _percent(count, previous),
            "dropoff": 0 if index == 0 else max(previous - count, 0),
        })
        previous = count

    now = timezone.now()
    stale_cutoff = now - timedelta(days=7)
    bottlenecks = (
        {"key": "registered", "label_fa": "عضو بدون سفارش", "label_en": "Registered without order", "count": Customer.objects.filter(contacts__user__is_active=True).exclude(assessment_orders__isnull=False).distinct().count(), "stale": Customer.objects.filter(contacts__user__is_active=True, updated_at__lt=stale_cutoff).exclude(assessment_orders__isnull=False).distinct().count()},
        {"key": "unpaid", "label_fa": "سفارش پرداخت‌نشده", "label_en": "Unpaid order", "count": Order.objects.filter(status="pending").exclude(manual_payment__status="pending").values("customer_id").distinct().count(), "stale": Order.objects.filter(status="pending", updated_at__lt=stale_cutoff).exclude(manual_payment__status="pending").values("customer_id").distinct().count()},
        {"key": "ready", "label_fa": "پرداخت‌شده و شروع‌نشده", "label_en": "Paid, not started", "count": Order.objects.filter(status="paid").exclude(user__exam_attempts__isnull=False).values("customer_id").distinct().count(), "stale": Order.objects.filter(status="paid", updated_at__lt=stale_cutoff).exclude(user__exam_attempts__isnull=False).values("customer_id").distinct().count()},
        {"key": "in_progress", "label_fa": "آزمون نیمه‌تمام", "label_en": "Incomplete assessment", "count": Attempt.objects.filter(status="in_progress").values("user_id").distinct().count(), "stale": Attempt.objects.filter(status="in_progress", updated_at__lt=stale_cutoff).values("user_id").distinct().count()},
    )
    case_counts = {row["stage"]: row["total"] for row in CustomerCase.objects.values("stage").annotate(total=Count("pk"))}
    cases = [
        {"key": key, "label_fa": label_fa, "label_en": label_en, "count": case_counts.get(key, 0)}
        for key, label_fa, label_en in CASE_STAGE_CHOICES
    ]
    since = now - timedelta(days=30)
    event_counts = list(CustomerEvent.objects.filter(occurred_at__gte=since).values("category").annotate(total=Count("pk")).order_by("-total"))
    for event in event_counts:
        event["label_fa"], event["label_en"] = EVENT_CATEGORY_LABELS.get(
            event["category"], (event["category"], event["category"].replace("_", " ").title())
        )
    return {
        "stages": stages,
        "bottlenecks": bottlenecks,
        "cases": cases,
        "events_30d": event_counts,
        "customers": Customer.objects.count(),
        "overall_conversion": _percent(completed, registered),
        "generated_at": now,
    }
