import json
from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from accounts.models import User
from core.sms import send_sms
from core.sms.backends import SMSDeliveryError
from .models import ManagementNotification, NotificationReceipt, PushSubscription


URGENT_SMS_CATEGORIES = {"payments"}


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
        webpush(
            subscription_info={"endpoint": subscription.endpoint, "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth}},
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=settings.WEB_PUSH_VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.WEB_PUSH_VAPID_SUBJECT},
            ttl=3600,
        )
        return ""
    except WebPushException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status in {404, 410}:
            subscription.is_active = False
            subscription.save(update_fields=["is_active", "updated_at"])
        return str(exc)[:240]


def _send_user_push(user, payload):
    errors = []
    for subscription in user.push_subscriptions.filter(is_active=True):
        error = _push(subscription, payload)
        if error:
            errors.append(error)
    return "; ".join(errors)[:240]


def process_notifications(now=None):
    now = now or timezone.now()
    if not settings.WEB_PUSH_VAPID_PRIVATE_KEY:
        return {"push": 0, "sms": 0, "reminders": 0}
    push_count = sms_count = reminder_count = 0
    fresh = NotificationReceipt.objects.select_related("notification", "user").filter(push_sent_at__isnull=True, notification__status="unread")
    for receipt in fresh:
        item = receipt.notification
        receipt.last_error = _send_user_push(receipt.user, {"title": item.title, "body": item.description, "url": item.target_url, "tag": f"rvion-{item.pk}", "urgent": item.category in URGENT_SMS_CATEGORIES})
        receipt.push_sent_at = now
        receipt.save(update_fields=["push_sent_at", "last_error"])
        push_count += 1

    urgent = ManagementNotification.objects.filter(category__in=URGENT_SMS_CATEGORIES, status="unread", receipts__sms_sent_at__isnull=True).distinct()
    for item in urgent:
        if not settings.MANAGEMENT_ALERT_SMS_RECIPIENTS:
            continue
        text = f"آرویون: {item.title}\n{item.description}\nبرای رسیدگی وارد پنل مدیریت شوید."
        delivered = True
        for mobile in settings.MANAGEMENT_ALERT_SMS_RECIPIENTS:
            try:
                send_sms(mobile, text)
            except (SMSDeliveryError, ValueError, RuntimeError):
                delivered = False
            else:
                sms_count += 1
        if delivered:
            item.receipts.update(sms_sent_at=now)

    cutoff = now - timedelta(seconds=settings.MANAGEMENT_REMINDER_SECONDS)
    due = NotificationReceipt.objects.select_related("notification", "user").filter(
        seen_at__isnull=True, push_sent_at__isnull=False, notification__status="unread", notification__created_at__lte=cutoff,
    ).filter(Q(last_reminded_at__isnull=True) | Q(last_reminded_at__lte=cutoff))
    for user_id in due.values_list("user_id", flat=True).distinct():
        user_due = due.filter(user_id=user_id)
        count = user_due.count()
        first = user_due.first()
        _send_user_push(first.user, {"title": "یادآوری آرویون", "body": f"{count} مورد تازه هنوز دیده نشده است.", "url": "/fa/management/notifications/", "tag": "rvion-hourly-reminder"})
        user_due.update(last_reminded_at=now)
        reminder_count += 1
    return {"push": push_count, "sms": sms_count, "reminders": reminder_count}
