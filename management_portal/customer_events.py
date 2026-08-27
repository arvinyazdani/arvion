from django.utils import timezone

from .models import CustomerEvent


def record_customer_event(
    *, customer, category, event_type, title_fa, title_en, description="",
    case=None, source=None, actor=None, occurred_at=None, metadata=None,
    dedupe_key=None,
):
    """Record one immutable event without making the ledger a second truth."""

    source_type = ""
    source_id = ""
    if source is not None:
        source_type = source._meta.label_lower
        source_id = str(source.pk)
        dedupe_key = dedupe_key or f"{source_type}:{source_id}:{event_type}"
    defaults = {
        "customer": customer,
        "case": case,
        "category": category,
        "event_type": event_type,
        "title_fa": title_fa,
        "title_en": title_en,
        "description": description,
        "source_type": source_type,
        "source_id": source_id,
        "actor": actor,
        "occurred_at": occurred_at or timezone.now(),
        "metadata": metadata or {},
    }
    if dedupe_key:
        event, _created = CustomerEvent.objects.get_or_create(dedupe_key=dedupe_key, defaults=defaults)
        return event
    return CustomerEvent.objects.create(**defaults)
