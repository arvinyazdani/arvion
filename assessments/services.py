from django.db import transaction
from django.utils import timezone

from .models import ExamEntitlement, Order, PaymentTransaction


@transaction.atomic
def verify_sandbox_payment(order_id):
    order = Order.objects.select_for_update().select_related("exam", "user").get(pk=order_id)
    if order.status == "paid":
        return order, False
    external_id = f"sandbox-{order.id}"
    payment, _ = PaymentTransaction.objects.get_or_create(
        external_id=external_id,
        defaults={"order": order, "gateway": "sandbox", "amount_irr": order.amount_irr},
    )
    if payment.amount_irr != order.amount_irr:
        order.status = "failed"
        order.save(update_fields=["status", "updated_at"])
        payment.status = "failed"
        payment.raw_response = {"reason": "amount_mismatch"}
        payment.save(update_fields=["status", "raw_response"])
        return order, False
    now = timezone.now()
    payment.status = "verified"
    payment.verified_at = now
    payment.raw_response = {"sandbox": True, "verified": True}
    payment.save(update_fields=["status", "verified_at", "raw_response"])
    order.status = "paid"
    order.paid_at = now
    order.save(update_fields=["status", "paid_at", "updated_at"])
    ExamEntitlement.objects.get_or_create(
        order=order,
        defaults={"user": order.user, "exam": order.exam, "attempts_remaining": 1},
    )
    return order, True
