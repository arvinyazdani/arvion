"""The only sanctioned way to create, read, update, expire, or delete a
`FormDraft`. Nothing outside this module should construct or save one
directly — this is where the field allowlist, the race-safe single-active-
draft rule, and the expiry lifecycle are enforced.

Scope for this phase: leads_contact only. No view, signal, or login path
calls into this module yet — that wiring is explicitly out of scope here.
"""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from services.models import Service

from .models import FormDraft, Lead

DRAFT_RETENTION_DAYS = 7

# Every field a draft is ever allowed to hold, and how each value is
# checked. Anything not listed here is rejected outright — never silently
# dropped, never silently stored.
_FIELD_VALIDATORS = {
    "leads_contact": {
        "request_type": lambda value: _in_choices(value, Lead.REQUEST_TYPES),
        "service_id": lambda value: _is_valid_service_id(value),
        "budget_range": lambda value: _in_choices(value, Lead.BUDGETS),
        "timeline": lambda value: _in_choices(value, Lead.TIMELINES),
        "preferred_contact": lambda value: _in_choices(value, Lead.CONTACT_METHODS),
    },
}

# Named explicitly (rather than only relying on "not in the allowlist")
# so a rejection can say plainly *why*: these are exactly the categories
# of data a FormDraft must never hold, regardless of form_type.
FORBIDDEN_FIELD_KEYS = frozenset((
    "name", "phone", "email_or_telegram", "business_name", "website_url",
    "message", "privacy_accept", "public_token", "session_key", "submission_token",
))

FORM_TYPE_STEP_COUNTS = {"leads_contact": 3}


class DraftValidationError(ValidationError):
    """Raised for an invalid owner, form_type, current_step, or field."""


def _in_choices(value, choices):
    try:
        return value in dict(choices)
    except TypeError:
        return False


def _is_valid_service_id(value):
    if value is None:
        return True
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return False
    return Service.objects.filter(pk=value, is_active=True).exists()


def _require_real_owner(owner):
    if owner is None or not getattr(owner, "is_authenticated", False) or not getattr(owner, "pk", None):
        raise DraftValidationError("A draft must belong to a real, authenticated account.")


def normalize_fields(form_type, raw_fields):
    """Return a clean dict containing only the allowed, validated keys for
    this form_type. Raises DraftValidationError on any unknown key or
    invalid value — never silently drops or coerces bad input."""
    validators = _FIELD_VALIDATORS.get(form_type)
    if validators is None:
        raise DraftValidationError(f"Unsupported form_type: {form_type!r}")
    if not isinstance(raw_fields, dict):
        raise DraftValidationError("fields must be a dict")

    unknown = set(raw_fields) - set(validators)
    if unknown:
        forbidden = unknown & FORBIDDEN_FIELD_KEYS
        if forbidden:
            raise DraftValidationError(f"Field(s) never allowed in a draft: {sorted(forbidden)}")
        raise DraftValidationError(f"Unknown field(s): {sorted(unknown)}")

    cleaned = {}
    for key, validator in validators.items():
        if key not in raw_fields:
            continue
        value = raw_fields[key]
        if not validator(value):
            raise DraftValidationError(f"Invalid value for {key!r}: {value!r}")
        cleaned[key] = value
    return cleaned


def _validate_current_step(form_type, current_step):
    step_count = FORM_TYPE_STEP_COUNTS.get(form_type)
    if step_count is None:
        raise DraftValidationError(f"Unsupported form_type: {form_type!r}")
    if not isinstance(current_step, int) or isinstance(current_step, bool) or not (0 <= current_step < step_count):
        raise DraftValidationError(f"current_step out of range for {form_type!r}: {current_step!r}")


def _expire_if_stale(draft, *, now=None):
    now = now or timezone.now()
    if draft.status in FormDraft.ACTIVE_STATUSES and draft.expires_at <= now:
        draft.status = "expired"
        draft.save(update_fields=["status", "updated_at"])
        return True
    return False


def get_active_draft(owner, form_type):
    """The owner's current open/submitting draft for this form_type, or
    None — never another account's draft, and never one whose expiry has
    already passed even if nothing has swept its status field yet."""
    if owner is None or not getattr(owner, "is_authenticated", False):
        return None
    draft = FormDraft.objects.filter(
        owner=owner, form_type=form_type, status__in=FormDraft.ACTIVE_STATUSES,
    ).first()
    if draft is None:
        return None
    now = timezone.now()
    if draft.expires_at <= now:
        _expire_if_stale(draft, now=now)
        return None
    return draft


def upsert_active_draft(*, owner, form_type, fields, current_step=0, demo_snapshot=None):
    """Race-safe, idempotent create-or-update of the one active draft for
    (owner, form_type). A stale (already-expired) existing draft is
    transitioned to "expired" first — never silently reused past its own
    expiry — and a fresh one is created in its place. `expires_at` is
    always recomputed to exactly `DRAFT_RETENTION_DAYS` from now, on every
    valid save.

    Never creates a draft for an anonymous/unauthenticated owner: that
    check happens before any query, let alone any write.
    """
    _require_real_owner(owner)
    if form_type not in FORM_TYPE_STEP_COUNTS:
        raise DraftValidationError(f"Unsupported form_type: {form_type!r}")
    _validate_current_step(form_type, current_step)
    cleaned_fields = normalize_fields(form_type, fields)
    cleaned_snapshot = dict(demo_snapshot) if demo_snapshot else {}

    with transaction.atomic():
        # Locking the owner row (not FormDraft itself) is enough: every
        # writer of this user's FormDraft goes through this same gate
        # first, which alone serializes read-modify-write access to their
        # single active row — mirrors the pattern already used for
        # single-session enforcement and OTP issuance elsewhere in this
        # project.
        locked_owner = owner.__class__.objects.select_for_update().get(pk=owner.pk)
        now = timezone.now()
        existing = FormDraft.objects.filter(
            owner=locked_owner, form_type=form_type, status__in=FormDraft.ACTIVE_STATUSES,
        ).first()
        if existing and existing.expires_at <= now:
            existing.status = "expired"
            existing.save(update_fields=["status", "updated_at"])
            existing = None

        expires_at = now + timedelta(days=DRAFT_RETENTION_DAYS)
        if existing:
            existing.current_step = current_step
            existing.fields = cleaned_fields
            existing.demo_snapshot = cleaned_snapshot
            existing.expires_at = expires_at
            existing.save(update_fields=["current_step", "fields", "demo_snapshot", "expires_at", "updated_at"])
            return existing
        return FormDraft.objects.create(
            owner=locked_owner, form_type=form_type, current_step=current_step,
            fields=cleaned_fields, demo_snapshot=cleaned_snapshot, expires_at=expires_at,
        )


def delete_draft(owner, draft_id):
    """Hard-deletes a draft, strictly scoped to its own owner — a draft_id
    belonging to a different account is never touched, and this never
    raises for a nonexistent/foreign id; it just deletes nothing."""
    if owner is None or not getattr(owner, "is_authenticated", False):
        return False
    deleted, _ = FormDraft.objects.filter(pk=draft_id, owner=owner).delete()
    return deleted > 0
