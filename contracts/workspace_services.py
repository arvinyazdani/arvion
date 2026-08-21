"""Application services for the unified customer project workspace."""

from __future__ import annotations

import hashlib
import secrets
import string

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.urls import reverse
from django.utils import timezone

from accounts.security import client_address
from core.sms import send_sms
from core.sms.backends import SMSDeliveryError, normalize_iran_mobile
from management_portal.models import CaseActivity, Customer, CustomerCase

from .models import (
    ContractProposal,
    GeneralTermsTemplate,
    GeneralTermsVersion,
    RoomAccessGrant,
    RoomDelivery,
    RoomEvent,
    SpecialistAssignment,
    SpecialistFormTemplate,
    SpecialistFormTemplateVersion,
)
from .questionnaires import completion, normalize_schema
from .services import DEFAULT_CLAUSES, add_default_clauses, publish_version


DEFAULT_GENERAL_TERMS = "\n\n".join(
    f"ماده {index} ـ {title}\n{body}"
    for index, (title, body) in enumerate(DEFAULT_CLAUSES, 1)
)
PASSWORD_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#"


def generate_access_password(length=14):
    if length < 12:
        raise ValueError("Workspace passwords must contain at least 12 characters.")
    # Guarantee a mixed password while keeping ambiguous glyphs out.
    required = [
        secrets.choice(string.ascii_uppercase.replace("I", "").replace("O", "")),
        secrets.choice(string.ascii_lowercase.replace("l", "")),
        secrets.choice("23456789"),
        secrets.choice("!@#"),
    ]
    remaining = [secrets.choice(PASSWORD_ALPHABET) for _ in range(length - len(required))]
    chars = required + remaining
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def normalize_mobile(value):
    try:
        return normalize_iran_mobile(value)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


@transaction.atomic
def create_general_terms_version(*, body, actor, title="شرایط عمومی پیمان", language="fa", change_note=""):
    body = str(body or "").strip()
    if not body:
        raise ValidationError("متن شرایط عمومی نمی‌تواند خالی باشد.")
    template, _ = GeneralTermsTemplate.objects.select_for_update().get_or_create(
        slug=f"default-{language}",
        defaults={"name": title, "language": language, "is_active": True},
    )
    number = (template.versions.aggregate(value=Max("number"))["value"] or 0) + 1
    version = GeneralTermsVersion.objects.create(
        template=template,
        number=number,
        title=title,
        body=body,
        change_note=str(change_note or "").strip()[:240],
        created_by=actor,
    )
    template.current_version = version
    template.is_active = True
    template.save(update_fields=("current_version", "is_active", "updated_at"))
    return version


def current_general_terms(language="fa"):
    return (
        GeneralTermsVersion.objects.select_related("template")
        .filter(template__language=language, template__is_active=True, template__current_version_id=models_f("pk"))
        .order_by("-created_at")
        .first()
    )


def models_f(field):
    # Local helper keeps the import surface small and avoids a module-level name
    # collision with contracts.models.
    from django.db.models import F

    return F(field)


@transaction.atomic
def ensure_general_terms(*, actor, language="fa"):
    version = current_general_terms(language)
    if version:
        return version
    return create_general_terms_version(
        body=DEFAULT_GENERAL_TERMS,
        actor=actor,
        language=language,
        change_note="نسخه پایه خودکار برای شروع پرونده‌های جدید",
    )


def _case_phone(case):
    for value in (
        case.phone,
        getattr(case.customer, "phone", "") if case.customer_id else "",
    ):
        if value:
            try:
                return normalize_mobile(value)
            except ValidationError:
                continue
    return ""


def _case_project_title(case):
    label = {"crm": "سامانه CRM", "clinic": "پلتفرم کلینیک", "lead": "پروژه اختصاصی", "general": "پروژه اختصاصی"}.get(case.kind, "پروژه اختصاصی")
    return f"{label} {case.customer_name}".strip()


@transaction.atomic
def ensure_case_workspace(*, case, actor):
    """Create the one active workspace used by a new case, idempotently."""

    case = CustomerCase.objects.select_for_update().select_related("customer", "source_content_type").get(pk=case.pk)
    proposal = case.contract_proposals.exclude(status__in=("accepted", "expired", "revoked")).order_by("-updated_at").first()
    if proposal:
        return proposal, False
    terms = ensure_general_terms(actor=actor, language="fa")
    phone = _case_phone(case)
    proposal = ContractProposal(
        customer_case=case,
        customer=case.customer,
        customer_name=case.customer_name,
        customer_phone=phone,
        customer_email=case.email,
        title="پرونده پیشنهاد و قرارداد پروژه",
        project_title=_case_project_title(case),
        project_scope=case.summary or "شرح دقیق پروژه پس از بررسی نیازسنجی پایه و تخصصی نهایی می‌شود.",
        amount_irr=0,
        payment_terms="مراحل پرداخت در شرایط خصوصی این پرونده مشخص می‌شود.",
        delivery_terms="زمان تحویل پس از تکمیل نیازسنجی و تأیید شرایط خصوصی مشخص می‌شود.",
        client_details="\n".join(filter(None, (
            f"نام مجموعه: {case.customer_name}",
            f"مخاطب: {case.contact_name}" if case.contact_name else "",
            f"کد پرونده: {case.code}",
        ))),
        general_terms_version=terms,
        general_terms=terms.body,
        private_terms="",
        created_by=actor,
    )
    source = case.source
    if case.kind == "crm" and getattr(source, "_meta", None) and source._meta.label_lower == "crm_orders.crmorder":
        proposal.crm_order = source
    proposal.save()
    add_default_clauses(proposal)
    log_room_event(proposal, "workspace_created", actor=actor)
    CaseActivity.objects.create(
        case=case,
        actor=actor,
        kind="system",
        title="فضای اختصاصی مشتری ساخته شد",
        body=proposal.project_title,
    )
    return proposal, True


@transaction.atomic
def create_specialist_template_version(*, proposal, schema, actor, name=None, change_note=""):
    proposal = ContractProposal.objects.select_for_update().select_related("customer_case").get(pk=proposal.pk)
    if proposal.status not in {"draft", "revoked"} or proposal.current_version:
        raise ValidationError("فرم تخصصی پرونده منتشرشده قابل تغییر نیست؛ ابتدا نسخه جدید پرونده بسازید.")
    normalized = normalize_schema(schema)
    assignment = SpecialistAssignment.objects.filter(proposal=proposal).select_related("version__template").first()
    if assignment and assignment.answers:
        raise ValidationError("فرم دارای پاسخ مشتری است و بدون ساخت نسخه جدید قابل جایگزینی نیست.")
    if assignment:
        template = assignment.version.template
        number = (template.versions.aggregate(value=Max("number"))["value"] or 0) + 1
    else:
        slug = f"case-{proposal.customer_case.code.lower() if proposal.customer_case_id else proposal.pk}"
        template, _ = SpecialistFormTemplate.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name or f"فرم تخصصی {proposal.project_title}",
                "service_kind": proposal.customer_case.kind if proposal.customer_case_id and proposal.customer_case.kind in {"crm", "clinic", "general"} else "general",
                "description": "فرم اختصاصی این پرونده مشتری",
            },
        )
        number = (template.versions.aggregate(value=Max("number"))["value"] or 0) + 1
    version = SpecialistFormTemplateVersion.objects.create(
        template=template,
        number=number,
        schema=normalized,
        change_note=str(change_note or "").strip()[:240],
        created_by=actor,
    )
    template.current_version = version
    template.save(update_fields=("current_version", "updated_at"))
    if assignment:
        assignment.version = version
        assignment.progress = completion(normalized, {})
        assignment.status = "draft"
        assignment.revision += 1
        assignment.save(update_fields=("version", "progress", "status", "revision", "updated_at"))
    else:
        assignment = SpecialistAssignment.objects.create(
            proposal=proposal,
            version=version,
            progress=completion(normalized, {}),
        )
    return assignment


def log_room_event(proposal, event_type, *, request=None, actor=None, access_grant=None, assignment=None, metadata=None):
    metadata = dict(metadata or {})
    ip_hash = ""
    user_agent = ""
    if request is not None:
        address = client_address(request)
        ip_hash = hashlib.sha256(address.encode()).hexdigest() if address else ""
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:300]
    event = RoomEvent.objects.create(
        proposal=proposal,
        access_grant=access_grant,
        assignment=assignment,
        event_type=event_type,
        metadata=metadata,
        actor=actor,
        ip_hash=ip_hash,
        user_agent=user_agent,
    )
    now = event.created_at
    ContractProposal.objects.filter(pk=proposal.pk).update(last_activity_at=now)
    if proposal.customer_id:
        Customer.objects.filter(pk=proposal.customer_id).update(updated_at=now)
    return event


@transaction.atomic
def create_access_grant(*, proposal, authorized_phone, raw_password, actor, expires_at=None):
    proposal = ContractProposal.objects.select_for_update().get(pk=proposal.pk)
    phone = normalize_mobile(authorized_phone)
    active = list(
        RoomAccessGrant.objects.select_for_update().filter(
            proposal=proposal,
            authorized_phone=phone,
            is_active=True,
        )
    )
    now = timezone.now()
    for item in active:
        item.is_active = False
        item.revoked_at = now
        item.save(update_fields=("is_active", "revoked_at", "updated_at"))
    credential_version = (
        RoomAccessGrant.objects.filter(proposal=proposal, authorized_phone=phone)
        .aggregate(value=Max("credential_version"))["value"]
        or 0
    ) + 1
    grant = RoomAccessGrant(
        proposal=proposal,
        authorized_phone=phone,
        credential_version=credential_version,
        expires_at=expires_at,
        created_by=actor,
    )
    grant.set_password(raw_password)
    grant.full_clean()
    grant.save()
    log_room_event(
        proposal,
        "access_rotated" if active else "access_created",
        actor=actor,
        access_grant=grant,
        metadata={"credential_version": credential_version, "phone_last4": phone[-4:]},
    )
    return grant


@transaction.atomic
def revoke_access_grant(*, grant, actor):
    grant = RoomAccessGrant.objects.select_for_update().select_related("proposal").get(pk=grant.pk)
    if grant.is_active:
        grant.is_active = False
        grant.revoked_at = timezone.now()
        grant.save(update_fields=("is_active", "revoked_at", "updated_at"))
        log_room_event(grant.proposal, "access_revoked", actor=actor, access_grant=grant)
    return grant


def _local_mobile(canonical):
    return "0" + canonical[2:] if canonical.startswith("98") else canonical


def workspace_access_url(proposal, *, absolute_base):
    return f"{absolute_base.rstrip('/')}{reverse('contracts:contract_access', args=[proposal.token])}"


def send_workspace_access(*, proposal, grant, recipient_phone, raw_password, actor, absolute_base):
    """Send newly-created credentials; delivery failure never removes access."""

    if grant.proposal_id != proposal.pk:
        raise ValidationError("دسترسی انتخاب‌شده متعلق به این پرونده نیست.")
    recipient = normalize_mobile(recipient_phone)
    delivery = RoomDelivery.objects.create(
        proposal=proposal,
        access_grant=grant,
        recipient_phone=recipient,
        channel="sms",
        status="queued",
        template_key="customer_workspace_invitation_v1",
        created_by=actor,
    )
    url = workspace_access_url(proposal, absolute_base=absolute_base)
    message = (
        "فضای اختصاصی پروژه شما در آرویون آماده است.\n"
        f"لینک: {url}\n"
        f"نام کاربری: {_local_mobile(grant.authorized_phone)}\n"
        f"رمز ورود: {raw_password}\n"
        "این اطلاعات محرمانه است."
    )
    try:
        result = send_sms(recipient, message)
    except (SMSDeliveryError, ValueError, RuntimeError) as exc:
        delivery.status = "failed"
        delivery.error_message = str(exc)[:240]
        delivery.save(update_fields=("status", "error_message"))
        log_room_event(
            proposal,
            "delivery_failed",
            actor=actor,
            access_grant=grant,
            metadata={"recipient_last4": recipient[-4:], "delivery_id": delivery.pk},
        )
        return delivery
    delivery.status = "sent"
    delivery.provider_reference = result.reference[:120]
    delivery.sent_at = timezone.now()
    delivery.save(update_fields=("status", "provider_reference", "sent_at"))
    log_room_event(
        proposal,
        "link_sent",
        actor=actor,
        access_grant=grant,
        metadata={"recipient_last4": recipient[-4:], "delivery_id": delivery.pk},
    )
    return delivery


@transaction.atomic
def publish_customer_workspace(*, proposal, actor):
    proposal = ContractProposal.objects.select_for_update().select_related("general_terms_version").get(pk=proposal.pk)
    assignment = SpecialistAssignment.objects.filter(proposal=proposal).select_related("version").first()
    if assignment is None or not assignment.version.schema:
        raise ValidationError("پیش از انتشار، فرم تخصصی این پرونده را آماده کنید.")
    if proposal.general_terms_version_id:
        proposal.general_terms = proposal.general_terms_version.body
        proposal.save(update_fields=("general_terms", "updated_at"))
    if not proposal.private_terms.strip():
        raise ValidationError("شرایط خصوصی پیمان باید پیش از انتشار کامل شود.")
    if not proposal.access_grants.filter(is_active=True).exists():
        raise ValidationError("حداقل یک دسترسی فعال برای مشتری لازم است.")
    return publish_version(proposal, actor)


def workspace_progress(proposal):
    assignment = SpecialistAssignment.objects.filter(proposal=proposal).select_related("version").first()
    specialist = completion(assignment.version.schema, assignment.answers) if assignment else {
        "is_complete": False,
        "percent": 0,
        "completed_section_count": 0,
        "total_sections": 0,
    }
    version = proposal.versions.filter(number=proposal.current_version).first() if proposal.current_version else None
    acknowledgements = set(version.room_acknowledgements.values_list("document", flat=True)) if version else set()
    accepted = bool(version and hasattr(version, "acceptance"))
    completed_steps = int(specialist["is_complete"]) + int("general" in acknowledgements) + int("private" in acknowledgements) + int(accepted)
    return {
        "specialist": specialist,
        "general_acknowledged": "general" in acknowledgements,
        "private_acknowledged": "private" in acknowledgements,
        "accepted": accepted,
        "completed_steps": completed_steps,
        "total_steps": 4,
        "percent": completed_steps * 25,
    }
