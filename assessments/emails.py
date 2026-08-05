import logging

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone

from .models import Order


logger = logging.getLogger(__name__)


def send_payment_confirmation_email(order, request, lang):
    """Send a retry-safe payment confirmation without blocking a completed payment."""
    if order.status != "paid" or order.confirmation_email_sent_at:
        return False
    receipt_path = reverse("accounts:payment_receipt", kwargs={"pk": order.pk})
    receipt_url = request.build_absolute_uri(f"{receipt_path}?lang={lang}")
    exam_title = order.exam.title_fa if lang == "fa" else order.exam.title_en
    if lang == "fa":
        subject = "تأیید پرداخت آزمون آرویون"
        message = (
            f"پرداخت شما برای «{exam_title}» تأیید شد.\n"
            f"مبلغ: {order.amount_irr} ریال\n"
            f"شناسه سفارش: {order.pk}\n\n"
            f"مشاهده و چاپ رسید:\n{receipt_url}\n\n"
            "این رسید فاکتور رسمی یا مالیاتی نیست."
        )
    else:
        subject = "Your Arvion assessment payment is confirmed"
        message = (
            f"Your payment for “{exam_title}” has been confirmed.\n"
            f"Amount: {order.amount_irr} IRR\n"
            f"Order ID: {order.pk}\n\n"
            f"View and print your receipt:\n{receipt_url}\n\n"
            "This receipt is not an official tax invoice."
        )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.user.email])
    except Exception:
        logger.exception("Payment confirmation email failed for order %s", order.pk)
        return False
    sent_at = timezone.now()
    updated = Order.objects.filter(pk=order.pk, confirmation_email_sent_at__isnull=True).update(
        confirmation_email_sent_at=sent_at,
    )
    if updated:
        order.confirmation_email_sent_at = sent_at
    return bool(updated)
