from datetime import timedelta

from django.db.models import Count, Sum
from django.utils import timezone
from traffic.models import ActiveVisitor, TrafficDay

from .models import Customer, CustomerCase, CustomerEvent
from .customer_segments import CASE_STAGE_CHOICES, apply_customer_filters


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
    cohort = Customer.objects.filter(contacts__user__is_active=True).distinct()
    registered = cohort.count()
    ordered = cohort.filter(assessment_orders__isnull=False).distinct().count()
    paid = cohort.filter(assessment_orders__status="paid").distinct().count()
    started = cohort.filter(assessment_orders__status="paid", assessment_orders__entitlement__attempt__started_at__isnull=False).distinct().count()
    completed = cohort.filter(assessment_orders__status="paid", assessment_orders__entitlement__attempt__status="completed").distinct().count()
    raw = (
        ("registered", "مشتری با حساب فعال", "Customer with active account", registered),
        ("ordered", "ثبت سفارش", "Order created", ordered),
        ("paid", "سفارش تأییدشده", "Approved order", paid),
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
    labels = (
        ("registered", "عضو بدون سفارش", "Registered without order"),
        ("unpaid", "سفارش پرداخت‌نشده", "Unpaid order"),
        ("ready", "دسترسی فعال و شروع‌نشده", "Active access, not started"),
        ("in_progress", "آزمون نیمه‌تمام", "Incomplete assessment"),
    )
    bottlenecks = []
    for key, fa, en in labels:
        members = apply_customer_filters(Customer.objects.all(), {"journey": key})
        stale = apply_customer_filters(Customer.objects.all(), {"journey": key, "inactive_days": "7"})
        bottlenecks.append({"key": key, "label_fa": fa, "label_en": en, "count": members.count(), "stale": stale.count()})
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
        "traffic_days": TrafficDay.objects.filter(date__gte=timezone.localdate() - timedelta(days=6)).order_by("-date"),
        "traffic": TrafficDay.objects.filter(date__gte=timezone.localdate() - timedelta(days=6)).aggregate(views=Sum("page_views"), visitor_days=Sum("unique_visitors")),
        "active_visitors": ActiveVisitor.objects.filter(last_seen__gte=now-timedelta(minutes=5)).count(),
    }
