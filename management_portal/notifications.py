import json
import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone
from django.urls import reverse

from accounts.models import User
from assessments.models import ManualPaymentSubmission, SupportTicket
from assessments.services import PaymentVerificationError, approve_manual_payment
from clinic_orders.models import ClinicOrder
from contracts.models import ContractProposal
from crm_orders.models import CrmOrder
from leads.models import Lead
from core.sms import send_sms
from core.sms.backends import SMSDeliveryError
from .models import CaseTask, CustomerCase, ManagementNotification, NotificationReceipt, PushSubscription


# Account verification and payment review both require prompt staff action.
# The unseen-receipt guard below prevents duplicate SMS after the manager has
# already opened the corresponding notification.
URGENT_SMS_CATEGORIES = {"accounts", "payments"}
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


def _create_sla_alerts(now):
    """Escalate genuinely overdue work once, without creating a notification loop."""
    payment_cutoff = now - timedelta(seconds=settings.PAYMENT_REVIEW_SLA_SECONDS)
    for payment in ManualPaymentSubmission.objects.filter(status="pending", updated_at__lte=payment_cutoff):
        item, created = ManagementNotification.objects.get_or_create(
            source_key=f"sla:payment:{payment.pk}",
            defaults={"category": "payments", "title": "تأیید پرداخت از مهلت عبور کرده است", "description": f"شماره پیگیری: {payment.reference_number}", "target_url": reverse("management_portal:approvals"), "role": "assessments"},
        )
        if created:
            create_receipts(item)

    support_cutoff = now - timedelta(seconds=settings.SUPPORT_FIRST_RESPONSE_SLA_SECONDS)
    for ticket in SupportTicket.objects.filter(status="open", created_at__lte=support_cutoff):
        item, created = ManagementNotification.objects.get_or_create(
            source_key=f"sla:support:{ticket.pk}",
            defaults={"category": "support", "title": "تیکت بدون پاسخ مانده است", "description": ticket.subject, "target_url": reverse("management_portal:assessment_support"), "role": "support"},
        )
        if created:
            create_receipts(item)

    sales_cutoff = now - timedelta(seconds=settings.SALES_FOLLOW_UP_SLA_SECONDS)
    sales_sources = (
        (Lead.objects.filter(status="new", created_at__lte=sales_cutoff), "lead", lambda item: item.business_name or item.name),
        (CrmOrder.objects.filter(status="new", created_at__lte=sales_cutoff), "crm", lambda item: item.organization_name),
        (ClinicOrder.objects.filter(status="new", created_at__lte=sales_cutoff), "clinic", lambda item: item.clinic_name),
        (ContractProposal.objects.filter(status__in=("sent", "review"), created_at__lte=sales_cutoff), "contract", lambda item: item.customer_name),
    )
    for queryset, source, label in sales_sources:
        for item in queryset:
            if source == "contract":
                target = (
                    reverse("management_portal:workspace_detail", args=[item.customer_case_id])
                    if item.customer_case_id
                    else reverse("management_portal:contract_detail", args=[item.pk])
                )
            else:
                target = reverse("management_portal:request_detail", args=[source, item.pk])
            notification, created = ManagementNotification.objects.get_or_create(
                source_key=f"sla:{source}:{item.pk}",
                defaults={"category": "sales" if source != "contract" else "contracts", "title": "پیگیری قرارداد از مهلت عبور کرده است" if source == "contract" else "فرم جدید نیازمند پیگیری است", "description": label(item), "target_url": target, "role": "sales" if source != "contract" else ""},
            )
            if created:
                create_receipts(notification)


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
                "due_at": now,
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

def process_notifications(now=None):
    now = now or timezone.now()
    auto_approved_count = _auto_approve_pending_payments(now)
    _create_sla_alerts(now)
    push_count = sms_count = reminder_count = 0
    for task in CaseTask.objects.select_related("case").filter(status="open", due_at__lte=now):
        item, created = ManagementNotification.objects.get_or_create(source_key=f"crm-task-overdue:{task.pk}:{task.due_at.isoformat()}", defaults={"category": "sales", "title": "وظیفه CRM عقب افتاده", "description": f"{task.case.customer_name}: {task.title}", "target_url": reverse("management_portal:crm_case_detail", args=[task.case_id]), "role": "sales"})
        if created: create_receipts(item)
    for case in CustomerCase.objects.filter(next_follow_up_at__lte=now).exclude(stage__in=("won", "lost")):
        item, created = ManagementNotification.objects.get_or_create(source_key=f"crm-followup:{case.pk}:{case.next_follow_up_at.isoformat()}", defaults={"category": "sales", "title": "موعد پیگیری مشتری", "description": case.customer_name, "target_url": reverse("management_portal:crm_case_detail", args=[case.pk]), "role": "sales"})
        if created: create_receipts(item)
    if settings.WEB_PUSH_VAPID_PRIVATE_KEY:
        fresh = NotificationReceipt.objects.select_related("notification", "user").filter(push_sent_at__isnull=True, notification__status="unread")
        for receipt in fresh:
            item = receipt.notification
            receipt.last_error = _send_user_push(receipt.user, {"title": item.title, "body": item.description, "url": reverse("management_portal:notification_open", args=[item.pk]), "tag": f"rvion-{item.pk}", "urgent": item.category in URGENT_SMS_CATEGORIES})
            receipt.push_sent_at = now
            receipt.save(update_fields=["push_sent_at", "last_error"])
            push_count += 1

    # If every recipient has already opened the alert, an SMS would only repeat
    # information the manager has acted on. Keep the immediate SMS path solely
    # for urgent receipts that are still unseen.
    urgent = ManagementNotification.objects.filter(
        category__in=URGENT_SMS_CATEGORIES,
        status="unread",
        receipts__sms_sent_at__isnull=True,
        receipts__seen_at__isnull=True,
    ).distinct()
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
    return {
        "auto_approved": auto_approved_count,
        "push": push_count,
        "sms": sms_count,
        "reminders": reminder_count,
    }
