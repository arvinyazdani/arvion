from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from accounts.models import User
from assessments.models import ManualPaymentSubmission, SupportTicket
from clinic_orders.models import ClinicOrder
from contracts.models import ContractAcceptance, ContractReview
from crm_orders.models import CrmOrder
from leads.models import Lead

from .models import ManagementNotification
from .notifications import create_receipts


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
    if created:
        notify(category="sales", title="درخواست همکاری جدید", description=instance.name, target_url=reverse("management_portal:request_detail", args=["lead", instance.pk]), role="sales", source_key=f"lead:{instance.pk}")


@receiver(post_save, sender=CrmOrder)
def new_crm(sender, instance, created, **kwargs):
    if created:
        notify(category="sales", title="نیازسنجی CRM جدید", description=instance.organization_name, target_url=reverse("management_portal:request_detail", args=["crm", instance.pk]), role="sales", source_key=f"crm:{instance.pk}")


@receiver(post_save, sender=ClinicOrder)
def new_clinic(sender, instance, created, **kwargs):
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


@receiver(post_save, sender=ContractReview)
def contract_review(sender, instance, created, **kwargs):
    if created:
        proposal = instance.version.proposal
        notify(category="contracts", title="بازخورد قرارداد ثبت شد", description=proposal.customer_name, target_url=reverse("management_portal:contract_detail", args=[proposal.pk]), role="", source_key=f"contract-review:{instance.pk}")


@receiver(post_save, sender=ContractAcceptance)
def contract_acceptance(sender, instance, created, **kwargs):
    if created:
        proposal = instance.version.proposal
        notify(category="contracts", title="قرارداد تأیید شد", description=proposal.customer_name, target_url=reverse("management_portal:contract_detail", args=[proposal.pk]), role="", source_key=f"contract-acceptance:{instance.pk}")
