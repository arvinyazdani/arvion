from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from accounts.models import User
from assessments.models import ManualPaymentSubmission, SupportTicket
from clinic_orders.models import ClinicOrder
from contracts.models import ContractAcceptance, ContractProposal, ContractReview
from crm_orders.models import CrmOrder, CrmSpecialistDiscovery
from leads.models import Lead

from .models import ManagementNotification
from .notifications import create_receipts
from .cases import link_document, sync_source_case


def notify(*, category, title, description, target_url, role, source_key):
    notification, created = ManagementNotification.objects.get_or_create(source_key=source_key, defaults={
        "category": category, "title": title, "description": description,
        "target_url": target_url, "role": role,
    })
    if created:
        transaction.on_commit(lambda: create_receipts(notification))


@receiver(post_save, sender=User)
def new_user(sender, instance, created, **kwargs):
    if created and not instance.is_staff:
        notify(category="accounts", title="عضویت کاربر جدید", description=instance.email, target_url=reverse("management_portal:approvals"), role="", source_key=f"user:{instance.pk}")


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
    if created:
        notify(category="payments", title="رسید پرداخت جدید", description=instance.reference_number, target_url=reverse("management_portal:approvals"), role="assessments", source_key=f"payment:{instance.pk}")


@receiver(post_save, sender=SupportTicket)
def new_ticket(sender, instance, created, **kwargs):
    if created:
        notify(category="support", title="تیکت پشتیبانی جدید", description=str(instance), target_url=reverse("management_portal:assessment_support"), role="support", source_key=f"support:{instance.pk}")


@receiver(post_save, sender=ContractProposal)
def contract_proposal_created(sender, instance, created, **kwargs):
    if created:
        from .models import CustomerCase
        case = CustomerCase.objects.filter(phone=instance.customer_phone).first() or (CustomerCase.objects.filter(email__iexact=instance.customer_email).first() if instance.customer_email else None)
        if case: link_document(case, instance, kind="contract", title=f"پیش‌نویس قرارداد: {instance.project_title}", actor=instance.created_by)


@receiver(post_save, sender=ContractReview)
def contract_review(sender, instance, created, **kwargs):
    if created:
        proposal = instance.version.proposal
        from .models import CustomerCase
        case = CustomerCase.objects.filter(phone=proposal.customer_phone).first() or (CustomerCase.objects.filter(email__iexact=proposal.customer_email).first() if proposal.customer_email else None)
        if case: link_document(case, proposal, kind="contract", title=f"قرارداد: {proposal.project_title}", actor=proposal.created_by)
        notify(category="contracts", title="بازخورد قرارداد ثبت شد", description=proposal.customer_name, target_url=reverse("management_portal:contract_detail", args=[proposal.pk]), role="", source_key=f"contract-review:{instance.pk}")


@receiver(post_save, sender=ContractAcceptance)
def contract_acceptance(sender, instance, created, **kwargs):
    if created:
        proposal = instance.version.proposal
        from .models import CustomerCase
        case = CustomerCase.objects.filter(phone=proposal.customer_phone).first() or (CustomerCase.objects.filter(email__iexact=proposal.customer_email).first() if proposal.customer_email else None)
        if case:
            link_document(case, proposal, kind="contract", title=f"قرارداد تأییدشده: {proposal.project_title}", actor=proposal.created_by)
            case.stage = "won"; case.save(update_fields=("stage", "updated_at"))
        notify(category="contracts", title="قرارداد تأیید شد", description=proposal.customer_name, target_url=reverse("management_portal:contract_detail", args=[proposal.pk]), role="", source_key=f"contract-acceptance:{instance.pk}")
