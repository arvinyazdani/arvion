"""Source-backed inbox presentation; domain decisions remain in their services."""
import re
from urllib.parse import urlsplit, urlunsplit

from django.urls import reverse
from django.utils import timezone
from django.db.models import Case, CharField, Exists, F, OuterRef, Value, When
from django.db.models.functions import Length, Replace, StrIndex, Substr
from assessments.models import ManualPaymentSubmission
from assessments.models import AttemptResult, SupportTicket
from accounts.models import User
from leads.models import Lead
from crm_orders.models import CrmOrder
from clinic_orders.models import ClinicOrder
from contracts.models import ContractAcceptance, ContractReview


def unique_work(queryset):
    """Collapse active reminders/resubmissions of one receipt, retain event history."""
    end = Case(When(source_key__contains=":resubmitted:", then=StrIndex("source_key", Value(":resubmitted:")) - 1), default=Length("source_key"))
    key = Case(
        When(category="payments", source_key__regex=r"^payment:[0-9]+(:resubmitted:[0-9]+)?$", then=Substr("source_key", 1, end)),
        When(category="payments", source_key__regex=r"^sla:payment:[0-9]+$", then=Replace("source_key", Value("sla:"), Value(""))),
        default=F("source_key"), output_field=CharField(),
    )
    keyed = queryset.annotate(inbox_work_key=key)
    newer = keyed.filter(inbox_work_key=OuterRef("inbox_work_key"), pk__gt=OuterRef("pk"))
    return keyed.alias(inbox_has_newer=Exists(newer)).filter(inbox_has_newer=False)


def payment_source_id(notification):
    if notification.category != "payments":
        return None
    match = re.fullmatch(r"(?:payment:([0-9]{1,18})(?::resubmitted:[0-9]+)?|sla:payment:([0-9]{1,18})|payment-auto-approved:([0-9]{1,18}))", notification.source_key)
    return int(next(value for value in match.groups() if value)) if match else None


def localized_target(target, lang):
    """Only internal paths, preserving query/fragment but matching the UI language."""
    try:
        parsed = urlsplit(target or "")
    except ValueError:
        return ""
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/") or parsed.path.startswith("//"):
        return ""
    if parsed.path.startswith("/admin/"):
        return ""
    path = re.sub(r"^/(?:fa|en)/", f"/{lang}/", parsed.path)
    return urlunsplit(("", "", path, parsed.query, parsed.fragment))


def present_sources(items, user, lang):
    """One receipt query for the whole page, never one per notification."""
    fa = lang == "fa"
    can_view = user.is_superuser or user.has_perm("assessments.view_manualpaymentsubmission")
    ids = {payment_source_id(item) for item in items} - {None}
    payments = {p.pk: p for p in ManualPaymentSubmission.objects.filter(pk__in=ids).select_related("order__user", "order__exam")} if ids else {}
    auto_users = {payments[payment_source_id(item)].order.user_id for item in items if item.source_key.startswith("payment-auto-approved:") and payment_source_id(item) in payments and not payments[payment_source_id(item)].order.customer_id}
    from .models import CustomerContact
    legacy_customers = {}
    if auto_users:
        for user_id, customer_id in CustomerContact.objects.filter(user_id__in=auto_users).values_list("user_id", "customer_id"):
            legacy_customers.setdefault(user_id, customer_id)
    contract_targets = {}
    for prefix, model in (("contract-review", ContractReview), ("contract-acceptance", ContractAcceptance)):
        contract_ids = [int(item.source_key.split(":")[1]) for item in items if re.fullmatch(prefix + r":[0-9]{1,18}", item.source_key)]
        if contract_ids:
            contract_targets.update({f"{prefix}:{pk}": proposal_id for pk, proposal_id in model.objects.filter(pk__in=contract_ids).values_list("pk", "version__proposal_id")})
    existing = {}
    for prefix, model in (("support", SupportTicket), ("user", User), ("mobile-verification", User), ("lead", Lead), ("crm", CrmOrder), ("clinic", ClinicOrder), ("assessment-result", AttemptResult)):
        source_ids = [int(item.source_key.split(":")[1]) for item in items if re.fullmatch(prefix + r":[0-9]{1,18}", item.source_key)]
        if source_ids:
            existing[prefix] = set(model.objects.filter(pk__in=source_ids).values_list("pk", flat=True))
    legacy = {
        "/admin/assessments/manualpaymentsubmission/": reverse("management_portal:approvals"),
        "/admin/accounts/user/": reverse("management_portal:approvals"),
        "/admin/assessments/supportticket/": reverse("management_portal:assessment_support"),
        **{f"/admin/{app}/{model}/": reverse("management_portal:request_list") + f"?kind={kind}"
           for app, model, kind in (("leads", "lead", "lead"), ("crm_orders", "crmorder", "crm"), ("clinic_orders", "clinicorder", "clinic"))},
    }
    for item in items:
        item.waiting_since = item.created_at
        item.source_details = []
        item.can_review_payment = False
        item.destination_label = "باز کردن جزئیات" if fa else "Open details"
        item.destination = localized_target(legacy.get(item.target_url, item.target_url), lang)
        payment_id = payment_source_id(item)
        if payment_id:
            payment = payments.get(payment_id)
            item.destination = ""
            if payment:
                item.waiting_since = payment.updated_at
                item.destination = reverse("management_portal:approvals") + f"?payment={payment.pk}#payment-{payment.pk}"
                item.destination_label = "بررسی همین رسید" if fa else "Review this receipt"
                item.source_details = [
                    ("مشتری" if fa else "Customer", payment.order.user.get_full_name() or payment.order.user.email),
                    ("واریزکننده" if fa else "Payer", payment.payer_name),
                    ("مبلغ سفارش" if fa else "Order amount", f"{payment.order.amount_irr:,} " + ("ریال" if fa else "IRR")),
                    ("پیگیری" if fa else "Reference", payment.reference_number),
                    ("زمان پرداخت" if fa else "Payment time", timezone.localtime(payment.paid_at).strftime("%Y/%m/%d %H:%M")),
                ]
                item.can_review_payment = payment.status == "pending" and not item.source_key.startswith("payment-auto-approved:")
                if not can_view:
                    item.destination = ""
                    item.source_details = []
                    item.can_review_payment = False
                # Auto-approval is an update about granted access, not a new receipt decision.
                customer_id = payment.order.customer_id or legacy_customers.get(payment.order.user_id)
                if item.source_key.startswith("payment-auto-approved:") and customer_id:
                    item.destination = reverse("management_portal:customer_assessment_detail", args=[customer_id, payment.order.user_id])
                    item.destination_label = "مشاهده دسترسی آزمون" if fa else "View assessment access"
        elif re.fullmatch(r"support:[0-9]{1,18}", item.source_key):
            item.destination = reverse("management_portal:assessment_support") + "?ticket=" + item.source_key.split(":")[1]
        elif re.fullmatch(r"(?:user|mobile-verification):[0-9]{1,18}", item.source_key):
            account_id = item.source_key.split(":")[1]
            item.destination = reverse("management_portal:approvals") + f"?account={account_id}" if item.requires_action else reverse("management_portal:customer_account_open", args=[account_id])
        elif re.fullmatch(r"(?:lead|crm|clinic):[0-9]{1,18}", item.source_key):
            kind, object_id = item.source_key.split(":")
            item.destination = reverse("management_portal:request_detail", args=[kind, object_id])
        elif item.source_key in contract_targets:
            item.destination = reverse("management_portal:contract_detail", args=[contract_targets[item.source_key]])
        parts = item.source_key.split(":")
        if len(parts) == 2 and re.fullmatch(r"[0-9]{1,18}", parts[1]):
            if parts[0] in existing and int(parts[1]) not in existing[parts[0]]:
                item.destination = ""
            if parts[0] in {"contract-review", "contract-acceptance"} and item.source_key not in contract_targets:
                item.destination = ""
        item.source_missing = not bool(item.destination)


def safe_inbox_return(value):
    """A back link may point only at our localized inbox, not an arbitrary URL."""
    try:
        parsed = urlsplit(value or "")
    except ValueError:
        return ""
    if not parsed.scheme and not parsed.netloc and re.fullmatch(r"/(fa|en)/management/notifications/", parsed.path):
        return value
    return ""
