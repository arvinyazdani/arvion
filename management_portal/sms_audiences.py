from dataclasses import dataclass

from django.db.models import Q

from accounts.models import User
from assessments.models import Attempt, ManualPaymentSubmission
from core.sms.backends import normalize_iran_mobile
from .followup_groups import ready_orders, unpaid_orders


AUDIENCE_LABELS = {
    "registered": ("عضو بدون سفارش", "Registered without an order"),
    "unpaid": ("سفارش پرداخت‌نشده", "Order awaiting payment"),
    "payment_review": ("پرداخت منتظر بررسی", "Payment awaiting review"),
    "ready": ("دسترسی فعال و شروع‌نشده", "Active access, not started"),
    "completed": ("نتیجه آماده", "Result ready"),
}


@dataclass(frozen=True)
class SMSAudience:
    key: str
    label_fa: str
    label_en: str
    recipients: tuple

    @property
    def count(self):
        return len(self.recipients)


def _normalized_numbers(values):
    numbers = []
    for value in values:
        try:
            number = normalize_iran_mobile(value)
        except ValueError:
            continue
        if number not in numbers:
            numbers.append(number)
    return tuple(numbers)


def resolve_sms_audience(key):
    if key not in AUDIENCE_LABELS:
        raise ValueError("unsupported audience")
    if key == "registered":
        values = User.objects.filter(
            is_staff=False, is_active=True, assessment_orders__isnull=True,
        ).exclude(Q(mobile__isnull=True) | Q(mobile="")).values_list("mobile", flat=True)
    elif key == "unpaid":
        values = unpaid_orders().exclude(Q(user__mobile__isnull=True) | Q(user__mobile="")).values_list("user__mobile", flat=True)
    elif key == "payment_review":
        values = ManualPaymentSubmission.objects.filter(status="pending").exclude(
            Q(order__user__mobile__isnull=True) | Q(order__user__mobile="")
        ).values_list("order__user__mobile", flat=True)
    elif key == "ready":
        values = ready_orders().exclude(
            Q(user__mobile__isnull=True) | Q(user__mobile="")
        ).values_list("user__mobile", flat=True)
    else:
        values = Attempt.objects.filter(status="completed").exclude(
            Q(user__mobile__isnull=True) | Q(user__mobile="")
        ).values_list("user__mobile", flat=True)
    labels = AUDIENCE_LABELS[key]
    return SMSAudience(key, labels[0], labels[1], _normalized_numbers(values))


def sms_audience_overview():
    return tuple(resolve_sms_audience(key) for key in AUDIENCE_LABELS)
