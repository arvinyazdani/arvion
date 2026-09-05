from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from assessments.models import Attempt, AttemptResult, ManualPaymentSubmission, Order, SupportTicket
from clinic_orders.models import ClinicOrder
from contracts.models import ContractAcceptance, ContractProposal, ContractReview
from crm_orders.models import CrmOrder, CrmSpecialistDiscovery
from leads.models import Lead

from .models import CaseActivity, CustomerContact, ManagementNotification
from .customer_events import record_customer_event
from .notifications import create_receipts
from .cases import link_customer_event, link_document, resolve_customer, sync_source_case


def notify(*, category, title, description, target_url, role, source_key, due_at=None, priority=None):
    if due_at is None:
        due_at = timezone.now() + timedelta(seconds={
            "payments": settings.PAYMENT_AUTO_APPROVE_SECONDS,
            "support": 4 * 60 * 60,
            "sales": 24 * 60 * 60,
            "contracts": 24 * 60 * 60,
            "accounts": 24 * 60 * 60,
        }.get(category, 24 * 60 * 60))
    notification, created = ManagementNotification.objects.get_or_create(source_key=source_key, defaults={
        "category": category, "title": title, "description": description,
        "target_url": target_url, "role": role, "due_at": due_at,
        "priority": priority or ManagementNotification.DEFAULT_PRIORITY_BY_CATEGORY.get(category, "normal"),
    })
    if created:
        transaction.on_commit(lambda: create_receipts(notification))


def _customer_for_user(user):
    contact = CustomerContact.objects.filter(user=user).select_related("customer").first()
    return contact.customer if contact else None


@receiver(post_save, sender=User)
def new_user(sender, instance, created, **kwargs):
    # Signup no longer depends on an SMS code, so an unverified mobile is the
    # normal state and must not raise a verification task for every customer.
    # get_or_create inside notify keeps subsequent profile saves idempotent.
    if not instance.is_staff and instance.is_active:
        notify(
            category="accounts", title="عضویت کاربر جدید", description=instance.email,
            target_url=reverse("management_portal:customer_account_open", args=[instance.pk]),
            role="", source_key=f"user:{instance.pk}",
        )


@receiver(post_save, sender=Lead)
def new_lead(sender, instance, created, **kwargs):
    sync_source_case(instance, kind="lead", customer_name=instance.business_name or instance.name, contact_name=instance.name, phone=instance.phone or "", email=instance.email_or_telegram if "@" in instance.email_or_telegram else "", summary=instance.message, document_title="درخواست همکاری اولیه")
    if created:
        notify(category="sales", title="درخواست همکاری جدید", description=instance.name, target_url=reverse("management_portal:request_detail", args=["lead", instance.pk]), role="sales", source_key=f"lead:{instance.pk}")


@receiver(post_save, sender=CrmOrder)
def new_crm(sender, instance, created, **kwargs):
    sync_source_case(instance, kind="crm", customer_name=instance.organization_name, contact_name=instance.contact_name, phone=instance.phone, email=instance.work_email, summary=instance.main_pain_points, document_title="فرم نیازسنجی اولیه CRM")
    if created:
        notify(category="sales", title="نیازسنجی CRM جدید", description=instance.organization_name, target_url=reverse("management_portal:request_detail", args=["crm", instance.pk]), role="sales", source_key=f"crm:{instance.pk}")


@receiver(post_save, sender=CrmSpecialistDiscovery)
def specialist_crm_submitted(sender, instance, **kwargs):
    if instance.status == "submitted":
        case = sync_source_case(instance.order, kind="crm", customer_name=instance.order.organization_name, contact_name=instance.order.contact_name, phone=instance.order.phone, email=instance.order.work_email, summary=instance.order.main_pain_points, document_title="فرم نیازسنجی اولیه CRM")
        link_document(case, instance, kind="specialist", title="فرم نیازسنجی تخصصی CRM")
        notify(category="sales", title="نیازسنجی تخصصی CRM تکمیل شد", description=instance.order.organization_name, target_url=reverse("management_portal:request_detail", args=["crm", instance.order_id]), role="sales", source_key=f"crm-specialist:{instance.pk}:submitted")


@receiver(post_save, sender=ClinicOrder)
def new_clinic(sender, instance, created, **kwargs):
    sync_source_case(instance, kind="clinic", customer_name=instance.clinic_name, contact_name=instance.contact_name, phone=instance.phone, email=instance.work_email, summary=instance.main_pain_points, document_title="فرم نیازسنجی اولیه کلینیک")
    if created:
        notify(category="sales", title="نیازسنجی کلینیک جدید", description=instance.clinic_name, target_url=reverse("management_portal:request_detail", args=["clinic", instance.pk]), role="sales", source_key=f"clinic:{instance.pk}")


@receiver(post_save, sender=ManualPaymentSubmission)
def new_payment(sender, instance, created, **kwargs):
    if created or instance.status == "pending":
        order = instance.order
        customer = order.customer or resolve_customer(
            customer_name=order.user.get_full_name() or order.user.email,
            contact_name=order.user.get_full_name() or order.user.email,
            phone=getattr(order.user, "mobile", ""), email=order.user.email, kind="person", user=order.user,
        )
        if not order.customer_id:
            order.customer = customer
            order.save(update_fields=("customer",))
        title = "رسید پرداخت ارسال شد" if created else "رسید پرداخت اصلاح و دوباره ارسال شد"
        link_customer_event(customer, instance, kind="payment", title=title, body=f"شماره پیگیری: {instance.reference_number}", customer_name=customer.name)
        record_customer_event(
            customer=customer, category="payment", event_type=f"payment_{instance.status}",
            title_fa=title, title_en="Payment receipt submitted", description=instance.reference_number,
            source=instance, occurred_at=instance.updated_at,
            dedupe_key=f"payment:{instance.pk}:{instance.status}:{int(instance.updated_at.timestamp())}",
        )
        source_key = f"payment:{instance.pk}" if created else f"payment:{instance.pk}:resubmitted:{int(instance.updated_at.timestamp())}"
        notify(category="payments", title="رسید پرداخت جدید" if created else "رسید پرداخت اصلاح‌شده", description=instance.reference_number, target_url=reverse("management_portal:approvals"), role="assessments", source_key=source_key)


@receiver(post_save, sender=SupportTicket)
def new_ticket(sender, instance, created, **kwargs):
    if created:
        customer = instance.order.customer if instance.order_id and instance.order.customer_id else None
        if not customer:
            contact = CustomerContact.objects.filter(user=instance.user).select_related("customer").first()
            customer = contact.customer if contact else resolve_customer(
                customer_name=instance.user.get_full_name() or instance.user.email,
                contact_name=instance.user.get_full_name() or instance.user.email,
                phone=getattr(instance.user, "mobile", ""), email=instance.user.email, kind="person", user=instance.user,
            )
        link_customer_event(customer, instance, kind="attachment", title="تیکت پشتیبانی جدید", body=instance.subject, customer_name=customer.name)
        notify(category="support", title="تیکت پشتیبانی جدید", description=str(instance), target_url=reverse("management_portal:assessment_support"), role="support", source_key=f"support:{instance.pk}")


@receiver(post_save, sender=ContractProposal)
def contract_proposal_created(sender, instance, created, **kwargs):
    if created:
        customer = instance.customer or resolve_customer(customer_name=instance.customer_name, contact_name=instance.customer_name, phone=instance.customer_phone, email=instance.customer_email)
        if not instance.customer_id:
            instance.customer = customer
            instance.save(update_fields=("customer",))
        link_customer_event(customer, instance, kind="contract", title=f"پیش‌نویس قرارداد: {instance.project_title}", actor=instance.created_by, customer_name=instance.customer_name, phone=instance.customer_phone, email=instance.customer_email)
        record_customer_event(customer=customer, category="contract", event_type="contract_created", title_fa="پیش‌نویس قرارداد ساخته شد", title_en="Contract draft created", description=instance.project_title, source=instance, actor=instance.created_by, occurred_at=instance.created_at)


@receiver(post_save, sender=ContractReview)
def contract_review(sender, instance, created, **kwargs):
    if created:
        proposal = instance.version.proposal
        customer = proposal.customer or resolve_customer(customer_name=proposal.customer_name, phone=proposal.customer_phone, email=proposal.customer_email)
        link_customer_event(customer, instance, kind="attachment", title="بازخورد قرارداد ثبت شد", body=proposal.project_title, actor=proposal.created_by, customer_name=proposal.customer_name)
        target_url = reverse("management_portal:workspace_detail", args=[proposal.customer_case_id]) if proposal.customer_case_id else reverse("management_portal:contract_detail", args=[proposal.pk])
        notify(category="contracts", title="بازخورد قرارداد ثبت شد", description=proposal.customer_name, target_url=target_url, role="", source_key=f"contract-review:{instance.pk}")


@receiver(post_save, sender=ContractAcceptance)
def contract_acceptance(sender, instance, created, **kwargs):
    if created:
        proposal = instance.version.proposal
        customer = proposal.customer or resolve_customer(customer_name=proposal.customer_name, phone=proposal.customer_phone, email=proposal.customer_email)
        case = link_customer_event(customer, instance, kind="attachment", title="قرارداد تأیید شد", body=proposal.project_title, actor=proposal.created_by, customer_name=proposal.customer_name)
        record_customer_event(customer=customer, case=case, category="contract", event_type="contract_accepted", title_fa="قرارداد تأیید شد", title_en="Contract accepted", description=proposal.project_title, source=instance, actor=proposal.created_by, occurred_at=instance.accepted_at)
        case.stage = "won"; case.save(update_fields=("stage", "updated_at"))
        target_url = reverse("management_portal:workspace_detail", args=[proposal.customer_case_id]) if proposal.customer_case_id else reverse("management_portal:contract_detail", args=[proposal.pk])
        notify(category="contracts", title="قرارداد تأیید شد", description=proposal.customer_name, target_url=target_url, role="", source_key=f"contract-acceptance:{instance.pk}")


@receiver(post_save, sender=Order)
def order_event(sender, instance, created, **kwargs):
    customer = instance.customer or _customer_for_user(instance.user)
    if not customer:
        return
    if created:
        record_customer_event(
            customer=customer, category="order", event_type="order_created",
            title_fa="سفارش آزمون ثبت شد", title_en="Assessment order created",
            description=instance.exam.title_en or instance.exam.title_fa, source=instance,
            occurred_at=instance.created_at, dedupe_key=f"order:{instance.pk}:created",
        )
    if instance.status == "paid":
        record_customer_event(
            customer=customer, category="payment", event_type="order_paid",
            title_fa="پرداخت سفارش تأیید شد", title_en="Payment approved",
            description=instance.exam.title_en or instance.exam.title_fa, source=instance,
            occurred_at=instance.paid_at or instance.updated_at,
            dedupe_key=f"order:{instance.pk}:paid",
        )


@receiver(post_save, sender=Attempt)
def attempt_event(sender, instance, created, **kwargs):
    transaction.on_commit(lambda: _record_attempt_event(instance.pk))


def _record_attempt_event(attempt_id):
    instance = Attempt.objects.select_related("entitlement__order__customer", "user", "exam").filter(pk=attempt_id).first()
    if not instance:
        return
    customer = instance.entitlement.order.customer or _customer_for_user(instance.user)
    if not customer:
        return
    state = "started" if instance.started_at else instance.status
    record_customer_event(
        customer=customer, category="assessment", event_type=f"assessment_{state}",
        title_fa="آزمون شروع شد" if instance.started_at else "دسترسی آزمون ساخته شد",
        title_en="Assessment started" if instance.started_at else "Assessment access created",
        description=instance.exam.title_fa, source=instance,
        occurred_at=instance.started_at or instance.created_at,
        dedupe_key=f"attempt:{instance.pk}:{state}",
    )


@receiver(post_save, sender=AttemptResult)
def result_event(sender, instance, created, **kwargs):
    if not created:
        return
    attempt = instance.attempt
    customer = attempt.entitlement.order.customer or _customer_for_user(attempt.user)
    if customer:
        record_customer_event(
            customer=customer, category="assessment", event_type="assessment_completed",
            title_fa="نتیجه آزمون آماده شد", title_en="Assessment result ready",
            description=f"{instance.level_code} · {instance.percentage}%", source=instance,
            occurred_at=instance.generated_at,
        )


@receiver(post_save, sender=CaseActivity)
def case_activity_event(sender, instance, created, **kwargs):
    if created and instance.case.customer_id:
        record_customer_event(
            customer=instance.case.customer, case=instance.case,
            category="task" if instance.kind == "task" else "communication" if instance.kind in {"call", "message", "meeting"} else "sales",
            event_type=f"case_{instance.kind}", title_fa=instance.title,
            title_en=instance.title, description=instance.body, source=instance,
            actor=instance.actor, occurred_at=instance.created_at,
        )
