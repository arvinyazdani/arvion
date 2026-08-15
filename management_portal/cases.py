import hashlib
import json

from django.contrib.contenttypes.models import ContentType
from django.forms.models import model_to_dict

from .models import CaseActivity, CaseDocument, CustomerCase


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


def sync_source_case(instance, *, kind, customer_name, contact_name="", phone="", email="", summary="", document_title="نیازسنجی اولیه"):
    content_type = ContentType.objects.get_for_model(instance)
    stage = STAGE_MAP.get(getattr(instance, "status", "new"), getattr(instance, "status", "new"))
    if stage not in dict(CustomerCase.STAGES): stage = "new"
    case, created = CustomerCase.objects.get_or_create(source_content_type=content_type, source_object_id=instance.pk, defaults={
        "kind": kind, "customer_name": customer_name, "contact_name": contact_name, "phone": phone or "", "email": email or "",
        "stage": stage, "summary": summary or "",
    })
    if not created:
        case.customer_name, case.contact_name, case.phone, case.email, case.stage = customer_name, contact_name, phone or "", email or "", stage
        if summary: case.summary = summary
        case.save(update_fields=("customer_name", "contact_name", "phone", "email", "stage", "summary", "updated_at"))
    data = snapshot(instance)
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False).encode()
    document, document_created = CaseDocument.objects.update_or_create(case=case, content_type=content_type, object_id=instance.pk, kind="initial", defaults={"title": document_title, "snapshot": data, "checksum": hashlib.sha256(raw).hexdigest()})
    if created: CaseActivity.objects.create(case=case, kind="system", title="پرونده مشتری ساخته شد", body=document_title)
    elif document_created: CaseActivity.objects.create(case=case, kind="document", title="سند به پرونده افزوده شد", body=document.title)
    return case


def link_document(case, instance, *, kind, title, actor=None):
    content_type = ContentType.objects.get_for_model(instance)
    data = snapshot(instance);raw = json.dumps(data, sort_keys=True, ensure_ascii=False).encode()
    document, created = CaseDocument.objects.update_or_create(case=case, content_type=content_type, object_id=instance.pk, kind=kind, defaults={"title": title, "snapshot": data, "checksum": hashlib.sha256(raw).hexdigest(), "created_by": actor})
    if created: CaseActivity.objects.create(case=case, kind="document", title="سند جدید", body=title, actor=actor)
    return document
