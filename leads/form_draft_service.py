"""The only sanctioned way to create, read, update, expire, or delete a
`FormDraft`. Nothing outside this module should construct or save one
directly — this is where the field allowlist, the race-safe single-active-
draft rule, the expiry lifecycle, and the demo-snapshot attach/clear rules
are enforced.

Scope for this phase: leads_contact only. No view, signal, or login path
calls into this module yet — that wiring is explicitly out of scope here.

Every `DraftValidationError` message below is a fixed, generic string with
no interpolated value or caller-supplied key name: both a submitted field
value and an unrecognized field's own name may be attacker-controlled, and
this module's exceptions are allowed to reach logs, admin error pages, or
(eventually) API responses. Categorization is via the `.code` attribute,
drawn only from this module's own fixed vocabulary — never from payload
content.
"""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from projects.demo_snapshots import build_demo_selection_snapshot
from projects.models import DemoSelection
from services.models import Service

from .models import FormDraft, Lead
from .models.form_draft import DRAFT_RETENTION_DAYS  # single source of truth

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

# Named explicitly (rather than only relying on "not in the allowlist") so
# normalize_fields can tell the two rejection categories apart internally;
# neither category ever echoes the actual key name back in the raised
# message — see the module docstring.
FORBIDDEN_FIELD_KEYS = frozenset((
    "name", "phone", "email_or_telegram", "business_name", "website_url",
    "message", "privacy_accept", "public_token", "session_key", "submission_token",
))

FORM_TYPE_STEP_COUNTS = {"leads_contact": 3}

# The exact, fixed shape build_demo_selection_snapshot must produce. Checked
# again here (defense in depth) before any snapshot is ever written to a
# draft, so a future change to that helper can never smuggle a forbidden
# key into FormDraft.demo_snapshot without this service also being updated.
_DEMO_SNAPSHOT_ALLOWED_KEYS = frozenset((
    "template_title_fa", "template_title_en", "category_fa", "category_en",
    "brand", "theme_fa", "theme_en", "personality_fa", "personality_en",
    "features_fa", "features_en", "demo_template_slug",
))


class DraftValidationError(ValidationError):
    """Raised for an invalid owner, form_type, current_step, field, or
    demo_selection. See the module docstring: messages never repeat
    caller-supplied content."""


def _reject(code, message):
    raise DraftValidationError(message, code=code)


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
        _reject("unauthenticated_owner", "A draft must belong to a real, authenticated account.")


def _require_supported_form_type(form_type):
    if form_type not in FORM_TYPE_STEP_COUNTS:
        _reject("unsupported_form_type", "Unsupported form_type.")


def normalize_fields(form_type, raw_fields):
    """Return a clean dict containing only the allowed, validated keys for
    this form_type. Raises DraftValidationError on any unknown key or
    invalid value — never silently drops or coerces bad input, and never
    echoes the offending key or value back in the exception."""
    validators = _FIELD_VALIDATORS.get(form_type)
    if validators is None:
        _reject("unsupported_form_type", "Unsupported form_type.")
    if not isinstance(raw_fields, dict):
        _reject("invalid_fields_type", "fields must be a dict.")

    unknown = set(raw_fields) - set(validators)
    if unknown:
        if unknown & FORBIDDEN_FIELD_KEYS:
            _reject("forbidden_field", "One or more fields are never allowed in a draft.")
        _reject("unknown_field", "One or more fields are not recognized.")

    cleaned = {}
    for key, validator in validators.items():
        if key not in raw_fields:
            continue
        value = raw_fields[key]
        if not validator(value):
            _reject("invalid_field_value", "One or more field values are invalid.")
        cleaned[key] = value
    return cleaned


def _validate_current_step(form_type, current_step):
    step_count = FORM_TYPE_STEP_COUNTS[form_type]
    if not isinstance(current_step, int) or isinstance(current_step, bool) or not (0 <= current_step < step_count):
        _reject("invalid_current_step", "current_step is out of range for this form_type.")


def _validate_snapshot_shape(snapshot):
    if not isinstance(snapshot, dict) or set(snapshot) != _DEMO_SNAPSHOT_ALLOWED_KEYS:
        _reject("invalid_snapshot_shape", "Demo snapshot has an unexpected shape.")


def _get_active_draft_locked(locked_owner, form_type, now):
    """Must only be called with `locked_owner` already `select_for_update()`-
    locked inside an open transaction. The only place an active draft's
    status is ever transitioned to "expired" as a write: everywhere else
    (get_active_draft) is read-only."""
    existing = FormDraft.objects.filter(
        owner=locked_owner, form_type=form_type, status__in=FormDraft.ACTIVE_STATUSES,
    ).first()
    if existing and existing.expires_at <= now:
        existing.status = "expired"
        existing.save(update_fields=["status", "updated_at"])
        existing = None
    return existing


def get_active_draft(owner, form_type):
    """The owner's current open/submitting, not-yet-expired draft for this
    form_type, or None — never another account's draft. Strictly
    read-only: never writes, never opens a transaction, never takes a
    row lock. A draft whose expiry has already passed is simply not
    returned here; transitioning it to "expired" happens only inside a
    locked write path (upsert_active_draft or a future cleanup job), never
    as a side effect of a read, so this can never race a concurrent
    renewal of the same row.
    """
    if owner is None or not getattr(owner, "is_authenticated", False):
        return None
    return FormDraft.objects.filter(
        owner=owner, form_type=form_type, status__in=FormDraft.ACTIVE_STATUSES,
        expires_at__gt=timezone.now(),
    ).first()


def upsert_active_draft(*, owner, form_type, fields, current_step=0):
    """Race-safe, idempotent create-or-update of the one active draft for
    (owner, form_type). A stale (already-expired) existing draft is
    transitioned to "expired" first — never silently reused past its own
    expiry — and a fresh one is created in its place. `expires_at` is
    always recomputed to exactly `DRAFT_RETENTION_DAYS` from now, on every
    valid save.

    Never creates a draft for an anonymous/unauthenticated owner: that
    check happens before any query, let alone any write.

    This never touches `demo_snapshot`: a newly created draft gets the
    model's own default (`{}`), and an existing draft keeps whatever
    snapshot it already had. Attaching or clearing a snapshot is done only
    through `attach_demo_snapshot`/`clear_demo_snapshot` below — there is
    no way to pass an arbitrary snapshot dict through this function.
    """
    _require_real_owner(owner)
    _require_supported_form_type(form_type)
    _validate_current_step(form_type, current_step)
    cleaned_fields = normalize_fields(form_type, fields)

    with transaction.atomic():
        # Locking the owner row (not FormDraft itself) is enough: every
        # writer of this user's FormDraft goes through this same gate
        # first, which alone serializes read-modify-write access to their
        # single active row — mirrors the pattern already used for
        # single-session enforcement and OTP issuance elsewhere in this
        # project.
        locked_owner = owner.__class__.objects.select_for_update().get(pk=owner.pk)
        now = timezone.now()
        existing = _get_active_draft_locked(locked_owner, form_type, now)

        expires_at = now + timedelta(days=DRAFT_RETENTION_DAYS)
        if existing:
            existing.current_step = current_step
            existing.fields = cleaned_fields
            existing.expires_at = expires_at
            existing.save(update_fields=["current_step", "fields", "expires_at", "updated_at"])
            return existing
        return FormDraft.objects.create(
            owner=locked_owner, form_type=form_type, current_step=current_step,
            fields=cleaned_fields, expires_at=expires_at,
        )


def attach_demo_snapshot(*, owner, form_type, demo_selection):
    """Attach a frozen, bilingual snapshot of `demo_selection` to the
    owner's current active draft. `demo_selection` must be a real, already
    saved `DemoSelection` instance — never a dict, never raw JSON, never
    anything a caller could shape freely. The snapshot itself is always
    produced by `build_demo_selection_snapshot` (never caller-supplied) and
    is checked against the exact expected key set before being written, so
    a draft can never end up holding a session_key/public_token/
    submission_token or any other unexpected structure.

    Session/ownership authorization of `demo_selection` (confirming it
    actually belongs to the request making this call) is the caller's
    responsibility in the phase that wires this up to a view — this
    service only guarantees the *shape* and *target* (the calling owner's
    own active draft) are safe.
    """
    _require_real_owner(owner)
    _require_supported_form_type(form_type)
    if not isinstance(demo_selection, DemoSelection) or demo_selection.pk is None:
        _reject("invalid_demo_selection", "demo_selection must be a saved DemoSelection instance.")
    snapshot = build_demo_selection_snapshot(demo_selection)
    _validate_snapshot_shape(snapshot)

    with transaction.atomic():
        locked_owner = owner.__class__.objects.select_for_update().get(pk=owner.pk)
        now = timezone.now()
        draft = _get_active_draft_locked(locked_owner, form_type, now)
        if draft is None:
            _reject("no_active_draft", "No active draft exists to attach a snapshot to.")
        draft.demo_snapshot = snapshot
        draft.save(update_fields=["demo_snapshot", "updated_at"])
        return draft


def clear_demo_snapshot(*, owner, form_type):
    """Explicitly clear the demo snapshot on the owner's current active
    draft, leaving `fields`/`current_step`/`expires_at` untouched. This is
    the only other sanctioned way `demo_snapshot` may change after
    creation — ordinary field saves via `upsert_active_draft` never touch
    it, by design.
    """
    _require_real_owner(owner)
    _require_supported_form_type(form_type)

    with transaction.atomic():
        locked_owner = owner.__class__.objects.select_for_update().get(pk=owner.pk)
        now = timezone.now()
        draft = _get_active_draft_locked(locked_owner, form_type, now)
        if draft is None:
            _reject("no_active_draft", "No active draft exists to clear a snapshot from.")
        draft.demo_snapshot = {}
        draft.save(update_fields=["demo_snapshot", "updated_at"])
        return draft


def delete_draft(owner, draft_id):
    """Hard-deletes a draft, strictly scoped to its own owner — a draft_id
    belonging to a different account is never touched, and this never
    raises for a nonexistent/foreign id; it just deletes nothing."""
    if owner is None or not getattr(owner, "is_authenticated", False):
        return False
    deleted, _ = FormDraft.objects.filter(pk=draft_id, owner=owner).delete()
    return deleted > 0
