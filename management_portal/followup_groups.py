"""Shared order-level predicates for reports, segments and SMS audiences."""
from django.db.models import Q
from django.utils import timezone

from assessments.models import Order


def ready_orders():
    return Order.objects.filter(
        status="paid", entitlement__isnull=False, entitlement__revoked_at__isnull=True,
        entitlement__attempts_remaining__gt=0, entitlement__attempt__isnull=True,
    ).filter(Q(entitlement__expires_at__isnull=True) | Q(entitlement__expires_at__gt=timezone.now()))


def unpaid_orders():
    return Order.objects.filter(status="pending").filter(
        Q(manual_payment__isnull=True) | Q(manual_payment__status="rejected")
    )
