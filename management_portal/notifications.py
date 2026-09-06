import json
import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone, translation
from django.urls import reverse

from accounts.models import User
from assessments.models import ManualPaymentSubmission
from assessments.services import PaymentVerificationError, approve_manual_payment
from core.sms import send_sms
from core.sms.backends import SMSDeliveryError
from .models import CaseTask, CustomerCase, ManagementNotification, NotificationReceipt, PushSubscription
from .templatetags.management_i18n import (
    management_notification_description,
    management_notification_title,
)


# Account verification and payment review both require prompt staff action.
# The unseen-receipt guard below prevents duplicate SMS after the manager has
# already opened the corresponding notification.
URGENT_SMS_CATEGORIES = {"payments"}
logger = logging.getLogger(__name__)


def recipients_for(notification):
    users = User.objects.filter(is_staff=True, is_active=True)
    if notification.role:
        users = users.filter(Q(is_superuser=True) | Q(groups__name=f"rvion_{notification.role}"))
    else:
        users = users.filter(is_superuser=True)
    return users.distinct()


def create_receipts(notification):
    NotificationReceipt.objects.bulk_create(
        [NotificationReceipt(user=user, notification=notification) for user in recipients_for(notification)],
        ignore_conflicts=True,
    )


def _push(subscription, payload):
    from pywebpush import WebPushException, webpush
    try:
        transport_payload = dict(payload)
        ttl = transport_payload.pop("ttl", 3600)
        webpush(
            subscription_info={"endpoint": subscription.endpoint, "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth}},
            data=json.dumps(transport_payload, ensure_ascii=False),
            vapid_private_key=settings.WEB_PUSH_VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.WEB_PUSH_VAPID_SUBJECT},
            ttl=ttl,
        )
        return ""
    except WebPushException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status in {404, 410}:
            subscription.is_active = False
            subscription.save(update_fields=["is_active", "updated_at"])
        logger.warning("Web push rejected for subscription %s: %s", subscription.pk, exc)
        return str(exc)[:240]
    except Exception as exc:
        # A network/DNS failure reaching the push service must not abort the
        # whole notification run: SMS, SLA alerts and reminders follow it.
        logger.exception("Web push transport failed for subscription %s", subscription.pk)
        return f"transport: {exc}"[:240]


def _send_user_push(user, payload):
    subscriptions = list(user.push_subscriptions.filter(is_active=True))
    if not subscriptions:
        return "no active push subscription"
    errors = []
    delivered = False
    for subscription in subscriptions:
        error = _push(subscription, payload)
        if error:
            errors.append(error)
        else:
            delivered = True
    # A receipt represents the user, not a single device. One accepted device
    # is enough; retrying would duplicate the alert on successful devices.
    return "" if delivered else "; ".join(errors)[:240]


def _language_for(user):
    return "en" if getattr(user, "preferred_language", "fa") == "en" else "fa"


def _notification_push_payload(user, item):
    """Build the out-of-page payload in the recipient's own panel language."""
    lang = _language_for(user)
    with translation.override(lang):
        target = reverse("management_portal:notification_open", args=[item.pk])
    return {
        "title": management_notification_title(item.title, lang),
        "body": management_notification_description(item.description, lang),
        "url": target,
        "tag": item.source_key.split(":resubmitted:", 1)[0].replace(":", "-"),
        "urgent": item.category in URGENT_SMS_CATEGORIES and item.requires_action,
        "priority": item.priority,
        "notification_id": item.pk,
        # A receipt waiting for a three-minute decision must not arrive as an
        # actionable stale alert long after the system has auto-approved it.
        "ttl": 180 if item.category == "payments" and item.requires_action else 3600,
    }


def _auto_approve_pending_payments(now):
    """Grant timed card-transfer access once the manager review window closes."""
    cutoff = now - timedelta(seconds=settings.PAYMENT_AUTO_APPROVE_SECONDS)
    candidate_ids = list(
        ManualPaymentSubmission.objects.filter(
            status="pending",
            updated_at__lte=cutoff,
            order__gateway="card_transfer",
            order__status="pending",
            order__terms_accepted_at__isnull=False,
        ).values_list("pk", flat=True)
    )
    approved_count = 0
    for payment_id in candidate_ids:
        try:
            payment, order, transaction_created, applied = approve_manual_payment(
                payment_id,
                reviewer=None,
                review_note="تأیید خودکار سیستم پس از پایان مهلت ۳ دقیقه‌ای بررسی مدیر",
                automatic=True,
            )
        except (ManualPaymentSubmission.DoesNotExist, PaymentVerificationError):
            logger.exception("Timed payment approval failed for submission %s", payment_id)
            continue
        if not applied:
            continue
        approved_count += 1
        ManagementNotification.objects.filter(
            Q(source_key=f"payment:{payment.pk}")
            | Q(source_key__startswith=f"payment:{payment.pk}:resubmitted:")
            | Q(source_key=f"sla:payment:{payment.pk}"),
            status__in=("unread", "read"),
        ).update(status="resolved", resolved_at=now)
        notification, created = ManagementNotification.objects.get_or_create(
            source_key=f"payment-auto-approved:{payment.pk}",
            defaults={
                "category": "payments",
                "title": "پرداخت توسط سیستم تأیید شد",
                "description": f"{payment.reference_number} · {order.user.email} · دسترسی آزمون صادر شد",
                "target_url": reverse("management_portal:approvals"),
                "role": "assessments",
                "due_at": None,
                "requires_action": False,
                "priority": "normal",
            },
        )
        if created:
            create_receipts(notification)
        if transaction_created:
            send_mail(
                "پرداخت شما تأیید شد",
                f"پرداخت سفارش {order.pk} پس از پایان زمان بررسی تأیید شد و دسترسی آزمون فعال است.\n{settings.SITE_URL}/fa/account/",
                settings.DEFAULT_FROM_EMAIL,
                [order.user.email],
                fail_silently=True,
            )
    return approved_count

def _deliver_pending_pushes(now, attempted_ids=None):
    """Send every undelivered push and retry the ones that previously failed.

    A receipt is only marked delivered when the transport accepted it, so a
    provider outage no longer permanently swallows the alert. `attempted_ids`
    keeps a single run from re-sending to the same receipt twice.
    """
    if not settings.WEB_PUSH_VAPID_PRIVATE_KEY:
        return 0
    delivered = 0
    pending = NotificationReceipt.objects.select_related("notification", "user").filter(
        push_sent_at__isnull=True,
        seen_at__isnull=True,
        notification__status__in=("unread", "read"),
    ).filter(
        Q(snoozed_until__isnull=True) | Q(snoozed_until__lte=now),
        Q(push_retry_at__isnull=True) | Q(push_retry_at__lte=now),
        dismissed_at__isnull=True,
    ).order_by("pk")
    if attempted_ids:
        pending = pending.exclude(pk__in=attempted_ids)
    for receipt in pending[:100]:
        if attempted_ids is not None:
            attempted_ids.add(receipt.pk)
        item = receipt.notification
        error = _send_user_push(receipt.user, _notification_push_payload(receipt.user, item))
        receipt.last_error = error
        if error:
            # Leave push_sent_at empty so the next run retries this receipt.
            receipt.push_attempt_count = min(receipt.push_attempt_count + 1, 12)
            delay = min(3600, 60 * (2 ** min(receipt.push_attempt_count - 1, 6)))
            receipt.push_retry_at = now + timedelta(seconds=delay)
            receipt.save(update_fields=["last_error", "push_attempt_count", "push_retry_at"])
            continue
        receipt.push_sent_at = now
        receipt.push_attempt_count = 0
        receipt.push_retry_at = None
        receipt.save(update_fields=["push_sent_at", "last_error", "push_attempt_count", "push_retry_at"])
        delivered += 1
    return delivered


def process_notifications(now=None):
    now = now or timezone.now()
    # Push first: auto-approval resolves the payment notification, and the push
    # query only sends unread items, so approving first silently dropped the
    # manager's payment alert entirely.
    attempted_push_ids = set()
    push_count = _deliver_pending_pushes(now, attempted_push_ids)
    auto_approved_count = _auto_approve_pending_payments(now)
    sms_count = reminder_count = 0
    for task in CaseTask.objects.select_related("case").filter(status="open", due_at__lte=now):
        item, created = ManagementNotification.objects.get_or_create(source_key=f"crm-task-overdue:{task.pk}:{task.due_at.isoformat()}", defaults={"category": "sales", "title": "وظیفه CRM عقب افتاده", "description": f"{task.case.customer_name}: {task.title}", "target_url": reverse("management_portal:crm_case_detail", args=[task.case_id]), "role": "sales"})
        if created: create_receipts(item)
    for case in CustomerCase.objects.filter(next_follow_up_at__lte=now).exclude(stage__in=("won", "lost")):
        item, created = ManagementNotification.objects.get_or_create(source_key=f"crm-followup:{case.pk}:{case.next_follow_up_at.isoformat()}", defaults={"category": "sales", "title": "موعد پیگیری مشتری", "description": case.customer_name, "target_url": reverse("management_portal:crm_case_detail", args=[case.pk]), "role": "sales"})
        if created: create_receipts(item)
    # SLA alerts raised above are delivered on the next run.
    push_count += _deliver_pending_pushes(now, attempted_push_ids)

    # If every recipient has already opened the alert, an SMS would only repeat
    # information the manager has acted on. Keep the immediate SMS path solely
    # for urgent receipts that are still unseen.
    urgent = ManagementNotification.objects.filter(
        category__in=URGENT_SMS_CATEGORIES,
        requires_action=True,
        status="unread",
        receipts__sms_sent_at__isnull=True,
        receipts__seen_at__isnull=True,
    ).filter(
        Q(receipts__snoozed_until__isnull=True) | Q(receipts__snoozed_until__lte=now),
        Q(receipts__sms_retry_at__isnull=True) | Q(receipts__sms_retry_at__lte=now),
        receipts__dismissed_at__isnull=True,
    ).distinct()
    for item in urgent:
        if not settings.MANAGEMENT_ALERT_SMS_RECIPIENTS:
            continue
        text = f"آرویون: {item.title}\n{item.description}\nبرای رسیدگی وارد پنل مدیریت شوید."
        delivered = True
        for mobile in settings.MANAGEMENT_ALERT_SMS_RECIPIENTS:
            try:
                send_sms(mobile, text)
            except (SMSDeliveryError, ValueError, RuntimeError) as error:
                delivered = False
                logger.error("Management alert SMS failed for notification %s: %s", item.pk, error)
            else:
                sms_count += 1
        if delivered:
            item.receipts.update(sms_sent_at=now, sms_attempt_count=0, sms_retry_at=None)
        else:
            for receipt in item.receipts.filter(sms_sent_at__isnull=True):
                receipt.sms_attempt_count = min(receipt.sms_attempt_count + 1, 12)
                delay = min(3600, 60 * (2 ** min(receipt.sms_attempt_count - 1, 6)))
                receipt.sms_retry_at = now + timedelta(seconds=delay)
                receipt.save(update_fields=["sms_attempt_count", "sms_retry_at"])

    cutoff = now - timedelta(seconds=settings.MANAGEMENT_REMINDER_SECONDS)
    due = NotificationReceipt.objects.select_related("notification", "user").filter(
        seen_at__isnull=True, push_sent_at__isnull=False, push_sent_at__lte=cutoff,
        dismissed_at__isnull=True,
        notification__requires_action=True,
        notification__status__in=("unread", "read"), notification__created_at__lte=cutoff,
    ).filter(
        Q(snoozed_until__isnull=True) | Q(snoozed_until__lte=now),
        Q(last_reminded_at__isnull=True) | Q(last_reminded_at__lte=cutoff),
    )
    for user_id in due.values_list("user_id", flat=True).distinct():
        user_due = due.filter(user_id=user_id)
        count = user_due.count()
        first = user_due.first()
        lang = _language_for(first.user)
        with translation.override(lang):
            reminder_url = reverse("management_portal:notification_list")
        error = _send_user_push(first.user, {
            "title": "Rvion reminder" if lang == "en" else "یادآوری آرویون",
            "body": f"{count} new item(s) are still unseen." if lang == "en" else f"{count} مورد تازه هنوز دیده نشده است.",
            "url": reminder_url,
            "tag": "rvion-hourly-reminder",
        })
        if not error:
            user_due.update(last_reminded_at=now)
            reminder_count += 1
    return {
        "auto_approved": auto_approved_count,
        "push": push_count,
        "sms": sms_count,
        "reminders": reminder_count,
    }
