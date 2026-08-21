import hashlib
import json

from django.contrib.contenttypes.models import ContentType
from django.forms.models import model_to_dict

from accounts.models import User
from core.sms.backends import normalize_iran_mobile

from .models import (
    CaseActivity,
    CaseDocument,
    CaseDocumentRevision,
    Customer,
    CustomerCase,
    CustomerContact,
)


STAGE_MAP = {"contacted": "discovery", "review": "proposal", "accepted": "won", "expired": "lost", "revoked": "lost"}


def _json_value(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "pk"):
        return value.pk
    return str(value)


def snapshot(instance):
    data = model_to_dict(instance)
    return json.loads(json.dumps(data, default=_json_value, ensure_ascii=False))


def normalize_customer_phone(value):
    """Use one canonical mobile identity without rejecting legacy landlines."""

    rendered = str(value or "").strip()
    if not rendered:
        return ""
    try:
        return normalize_iran_mobile(rendered)
    except ValueError:
        return rendered


def _phone_candidates(value):
    canonical = normalize_customer_phone(value)
    if not canonical:
        return ()
    if canonical.startswith("98") and len(canonical) == 12:
        local = "0" + canonical[2:]
        return (canonical, local, f"+{canonical}", f"00{canonical}")
    return (canonical,)


def _snapshot_checksum(data):
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _record_document_revision(document, *, title, data, checksum):
    if not checksum:
        checksum = _snapshot_checksum(data)
    return CaseDocumentRevision.objects.get_or_create(
        document=document,
        checksum=checksum,
        defaults={"title": title, "snapshot": data},
    )


def _upsert_document(*, case, instance, kind, title, actor=None):
    content_type = ContentType.objects.get_for_model(instance)
    data = snapshot(instance)
    checksum = _snapshot_checksum(data)
    document = CaseDocument.objects.filter(
        case=case,
        content_type=content_type,
        object_id=instance.pk,
        kind=kind,
    ).first()
    created = document is None
    if document is None:
        document = CaseDocument.objects.create(
            case=case,
            content_type=content_type,
            object_id=instance.pk,
            kind=kind,
            title=title,
            snapshot=data,
            checksum=checksum,
            created_by=actor,
        )
    else:
        # Preserve a legacy/current value even if the backfill has not run yet.
        if document.snapshot:
            _record_document_revision(
                document,
                title=document.title,
                data=document.snapshot,
                checksum=document.checksum,
            )
        changed = document.checksum != checksum or document.title != title
        if changed:
            document.title = title
            document.snapshot = data
            document.checksum = checksum
            if actor and not document.created_by_id:
                document.created_by = actor
                document.save(
                    update_fields=("title", "snapshot", "checksum", "created_by")
                )
            else:
                document.save(update_fields=("title", "snapshot", "checksum"))
    _record_document_revision(
        document,
        title=title,
        data=data,
        checksum=checksum,
    )
    return document, created


def resolve_customer(*, customer_name, contact_name="", phone="", email="", kind="company", user=None):
    """Return the canonical customer and make sure the submitted contact is retained.

    Forms use different vocabulary for the same organisation.  Phone and email are
    stronger identifiers than the display name, while the latter remains a useful
    fallback for legacy submissions.
    """
    phone = normalize_customer_phone(phone)
    email = (email or "").strip().lower()
    customer = None
    if phone:
        customer = Customer.objects.filter(phone__in=_phone_candidates(phone)).first()
    if not customer and email:
        customer = Customer.objects.filter(email__iexact=email).first()
    # A display name is not an identity.  Keep the fallback only for legacy rows
    # that provide no phone or email at all.
    if not customer and customer_name and not (phone or email):
        customer = Customer.objects.filter(name__iexact=customer_name.strip()).first()
    if not customer:
        customer = Customer.objects.create(name=(customer_name or contact_name or email or phone or "مشتری جدید").strip(), kind=kind, phone=phone, email=email)
    else:
        changed = []
        if phone and (not customer.phone or normalize_customer_phone(customer.phone) == phone):
            if customer.phone != phone:
                customer.phone = phone; changed.append("phone")
        if email and not customer.email:
            customer.email = email; changed.append("email")
        if changed:
            changed.append("updated_at")
            customer.save(update_fields=changed)

    contact_name = (contact_name or customer_name or customer.name).strip()
    linked_user = user
    if linked_user is None and (email or phone):
        query = User.objects.all()
        if email:
            linked_user = query.filter(email__iexact=email).first()
        if linked_user is None and phone:
            linked_user = query.filter(mobile__in=_phone_candidates(phone)).first()
    if contact_name:
        contacts = CustomerContact.objects.filter(customer=customer)
        contact = contacts.filter(user=linked_user).first() if linked_user else None
        if contact is None and email:
            contact = contacts.filter(email__iexact=email).first()
        if contact is None and phone:
            contact = contacts.filter(phone__in=_phone_candidates(phone)).first()
        if contact is None and not (phone or email):
            contact = contacts.filter(name__iexact=contact_name).first()
        if not contact:
            CustomerContact.objects.create(customer=customer, name=contact_name, phone=phone, email=email, user=linked_user, is_primary=not customer.contacts.exists())
        else:
            changed = []
            if linked_user and not contact.user_id:
                contact.user = linked_user; changed.append("user")
            if phone and (not contact.phone or normalize_customer_phone(contact.phone) == phone) and contact.phone != phone:
                contact.phone = phone; changed.append("phone")
            if email and not contact.email:
                contact.email = email; changed.append("email")
            if changed:
                changed.append("updated_at")
                contact.save(update_fields=changed)
    return customer


def case_for_customer(customer, *, customer_name="", contact_name="", phone="", email=""):
    """Use the newest live case, or create a small operational case for service events."""
    case = customer.cases.exclude(stage__in=("won", "lost")).order_by("-updated_at").first() or customer.cases.order_by("-updated_at").first()
    if case:
        return case
    return CustomerCase.objects.create(
        customer=customer, kind="general", customer_name=customer_name or customer.name,
        contact_name=contact_name, phone=phone or customer.phone, email=email or customer.email,
        summary="پرونده عملیاتی ایجادشده از رویداد خدمات مشتری",
    )


def sync_source_case(instance, *, kind, customer_name, contact_name="", phone="", email="", summary="", document_title="نیازسنجی اولیه"):
    content_type = ContentType.objects.get_for_model(instance)
    phone = normalize_customer_phone(phone)
    stage = STAGE_MAP.get(getattr(instance, "status", "new"), getattr(instance, "status", "new"))
    if stage not in dict(CustomerCase.STAGES): stage = "new"
    customer = resolve_customer(customer_name=customer_name, contact_name=contact_name, phone=phone, email=email, kind="person" if kind == "lead" else "company")
    case, created = CustomerCase.objects.get_or_create(source_content_type=content_type, source_object_id=instance.pk, defaults={
        "customer": customer,
        "kind": kind, "customer_name": customer_name, "contact_name": contact_name, "phone": phone or "", "email": email or "",
        "stage": stage, "summary": summary or "",
    })
    if not created:
        case.customer, case.customer_name, case.contact_name, case.phone, case.email, case.stage = customer, customer_name, contact_name, phone or "", email or "", stage
        if summary: case.summary = summary
        case.save(update_fields=("customer", "customer_name", "contact_name", "phone", "email", "stage", "summary", "updated_at"))
    document, document_created = _upsert_document(
        case=case,
        instance=instance,
        kind="initial",
        title=document_title,
    )
    if created: CaseActivity.objects.create(case=case, kind="system", title="پرونده مشتری ساخته شد", body=document_title)
    elif document_created: CaseActivity.objects.create(case=case, kind="document", title="سند به پرونده افزوده شد", body=document.title)
    return case


def link_document(case, instance, *, kind, title, actor=None):
    document, created = _upsert_document(
        case=case,
        instance=instance,
        kind=kind,
        title=title,
        actor=actor,
    )
    if created: CaseActivity.objects.create(case=case, kind="document", title="سند جدید", body=title, actor=actor)
    return document


def link_customer_event(customer, instance, *, kind, title, body="", actor=None, customer_name="", contact_name="", phone="", email=""):
    """Attach a service event (payment, ticket, contract) to the customer timeline."""
    case = case_for_customer(customer, customer_name=customer_name, contact_name=contact_name, phone=phone, email=email)
    document = link_document(case, instance, kind=kind, title=title, actor=actor)
    CaseActivity.objects.get_or_create(
        case=case, kind="system", title=title, body=body or title,
        metadata={"content_type": document.content_type_id, "object_id": instance.pk, "kind": kind},
    )
    return case
