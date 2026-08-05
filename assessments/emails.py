import logging

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone

from .models import AttemptResult, Order


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
            f"مبلغ نهایی: {order.amount_irr:,} ریال\n"
            f"تخفیف: {order.discount_percent}٪\n"
            f"شناسه سفارش: {order.pk}\n\n"
            f"مشاهده و چاپ رسید:\n{receipt_url}\n\n"
            "این رسید فاکتور رسمی یا مالیاتی نیست."
        )
    else:
        subject = "Your Arvion assessment payment is confirmed"
        message = (
            f"Your payment for “{exam_title}” has been confirmed.\n"
            f"Final amount: {order.amount_irr:,} IRR\n"
            f"Discount: {order.discount_percent}%\n"
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


def send_result_ready_email(result, request, lang):
    """Email report links once while keeping result delivery independent from SMTP."""
    if result.report_email_sent_at:
        return False
    report_path = reverse("assessments:result", kwargs={"pk": result.pk})
    report_url = request.build_absolute_uri(f"{report_path}?lang={lang}")
    certificate_url = request.build_absolute_uri(f"{result.certificate.get_absolute_url()}?lang={lang}")
    exam_title = result.attempt.exam.title_fa if lang == "fa" else result.attempt.exam.title_en
    level = result.level_title_fa if lang == "fa" else result.level_title_en
    if lang == "fa":
        subject = "نتیجه آزمون آرویون آماده است"
        message = (
            f"نتیجه «{exam_title}» آماده است.\n"
            f"نمره: {result.percentage} از ۱۰۰\nسطح: {level}\n\n"
            f"گزارش خصوصی و تحلیل پاسخ‌ها:\n{report_url}\n\n"
            f"گواهی قابل اعتبارسنجی:\n{certificate_url}\n\n"
            "این نتیجه و گواهی رسمی یا دانشگاهی نیستند."
        )
    else:
        subject = "Your Arvion assessment result is ready"
        message = (
            f"Your result for “{exam_title}” is ready.\n"
            f"Score: {result.percentage} out of 100\nLevel: {level}\n\n"
            f"Private report and answer analysis:\n{report_url}\n\n"
            f"Verifiable certificate:\n{certificate_url}\n\n"
            "This result and certificate are not official or academic credentials."
        )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [result.attempt.user.email])
    except Exception:
        logger.exception("Result-ready email failed for result %s", result.pk)
        return False
    sent_at = timezone.now()
    updated = AttemptResult.objects.filter(pk=result.pk, report_email_sent_at__isnull=True).update(
        report_email_sent_at=sent_at,
    )
    if updated:
        result.report_email_sent_at = sent_at
    return bool(updated)
