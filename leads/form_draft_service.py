"""The only sanctioned way to create, read, update, expire, or delete a
`FormDraft`. Nothing outside this module should construct or save one
directly — this is where the field allowlist, the race-safe single-active-
draft rule, the expiry lifecycle, and the demo-snapshot attach/clear rules
are enforced.

Scope: leads_contact only. `leads.signals` (pre-login hand-off) and
`leads.views.contact.LeadCreateView` (already-authenticated hand-off) are
the only callers outside this module and its own tests — no auto-save
endpoint, restore/delete UI, or Lead-submission wiring exists yet.

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
# key, an oversized value, or a wrong-typed value into FormDraft.demo_snapshot
# without this service also being updated.
_DEMO_SNAPSHOT_TEXT_KEYS = (
    "template_title_fa", "template_title_en", "category_fa", "category_en",
    "brand", "theme_fa", "theme_en", "personality_fa", "personality_en",
    "demo_template_slug",
)
_DEMO_SNAPSHOT_FEATURE_KEYS = ("features_fa", "features_en")
_DEMO_SNAPSHOT_ALLOWED_KEYS = frozenset(_DEMO_SNAPSHOT_TEXT_KEYS + _DEMO_SNAPSHOT_FEATURE_KEYS)
_MAX_SNAPSHOT_TEXT_LENGTH = 300
_MAX_SNAPSHOT_FEATURE_LENGTH = 200
_MAX_SNAPSHOT_FEATURE_COUNT = 20


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


def _is_safe_snapshot_string(value):
    # bool/int/bytes/list/dict all fail isinstance(value, str) outright; a
    # generous, fixed length cap is defense in depth against a future
    # change to the snapshot builder producing unbounded text.
    return isinstance(value, str) and len(value) <= _MAX_SNAPSHOT_TEXT_LENGTH


def _is_safe_feature_list(value):
    return (
        isinstance(value, list)
        and len(value) <= _MAX_SNAPSHOT_FEATURE_COUNT
        and all(isinstance(item, str) and len(item) <= _MAX_SNAPSHOT_FEATURE_LENGTH for item in value)
    )


def _validate_snapshot_shape(snapshot):
    """Full-value validation, not just key-set validation: every text field
    must be a plain, length-bounded string (never a nested mapping/list,
    bytes, number, or bool), both feature lists must be length-bounded
    lists of length-bounded strings, and the two feature lists must be the
    same length. Never reveals the offending value in its error message."""
    if not isinstance(snapshot, dict) or set(snapshot) != _DEMO_SNAPSHOT_ALLOWED_KEYS:
        _reject("invalid_snapshot_shape", "Demo snapshot has an unexpected shape.")
    for key in _DEMO_SNAPSHOT_TEXT_KEYS:
        if not _is_safe_snapshot_string(snapshot[key]):
            _reject("invalid_snapshot_shape", "Demo snapshot has an unexpected shape.")
    for key in _DEMO_SNAPSHOT_FEATURE_KEYS:
        if not _is_safe_feature_list(snapshot[key]):
            _reject("invalid_snapshot_shape", "Demo snapshot has an unexpected shape.")
    if len(snapshot["features_fa"]) != len(snapshot["features_en"]):
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


def ensure_active_draft(*, owner, form_type):
    """Return the owner's current active draft for `form_type`, creating an
    empty one (default `fields={}`, `current_step=0`, `demo_snapshot={}`)
    if none exists yet. Never modifies `fields`/`current_step`/
    `demo_snapshot` on an already-existing draft — this only guarantees
    one exists, it never upserts content the way `upsert_active_draft`
    does. An existing-but-expired draft is transitioned to `"expired"`
    and replaced with a fresh one, exactly like every other write path
    here. Race-safe via the same owner-row lock; repeated calls converge
    on the same single row rather than ever creating a second one."""
    _require_real_owner(owner)
    _require_supported_form_type(form_type)
    with transaction.atomic():
        locked_owner = owner.__class__.objects.select_for_update().get(pk=owner.pk)
        now = timezone.now()
        existing = _get_active_draft_locked(locked_owner, form_type, now)
        if existing is not None:
            return existing
        return FormDraft.objects.create(
            owner=locked_owner, form_type=form_type, expires_at=now + timedelta(days=DRAFT_RETENTION_DAYS),
        )


def ensure_active_draft_with_demo_snapshot(*, owner, form_type, demo_selection):
    """Atomically ensure an active draft exists for (owner, form_type) and
    attach `demo_selection`'s snapshot to it — both steps under the same
    owner-row lock and the same transaction, so a concurrent delete/expire
    of the just-ensured draft between "ensure" and "attach" is impossible.
    Unlike `attach_demo_snapshot`, this never raises `no_active_draft`: if
    no active draft exists yet, one is created with the snapshot already
    attached in a single write. An existing draft's `fields`/`current_step`
    are left untouched, exactly like `attach_demo_snapshot`.

    `demo_selection` is validated and re-read fresh from the database the
    same way `attach_demo_snapshot` does — see `_reload_demo_selection`.
    """
    _require_real_owner(owner)
    _require_supported_form_type(form_type)
    fresh_selection = _reload_demo_selection(demo_selection)
    if fresh_selection is None:
        _reject("invalid_demo_selection", "demo_selection must be a saved DemoSelection instance.")
    snapshot = build_demo_selection_snapshot(fresh_selection)
    _validate_snapshot_shape(snapshot)

    with transaction.atomic():
        locked_owner = owner.__class__.objects.select_for_update().get(pk=owner.pk)
        now = timezone.now()
        existing = _get_active_draft_locked(locked_owner, form_type, now)
        expires_at = now + timedelta(days=DRAFT_RETENTION_DAYS)
        if existing is None:
            return FormDraft.objects.create(
                owner=locked_owner, form_type=form_type, demo_snapshot=snapshot, expires_at=expires_at,
            )
        existing.demo_snapshot = snapshot
        existing.expires_at = expires_at
        existing.save(update_fields=["demo_snapshot", "expires_at", "updated_at"])
        return existing


def _reload_demo_selection(demo_selection):
    """Never trust the caller's in-memory `DemoSelection` instance — its
    `selections` (or any other field) may have been mutated locally
    without being saved. Re-reading by primary key guarantees
    `build_demo_selection_snapshot` only ever sees what is actually
    persisted, and also catches a since-deleted row. Returns None for an
    invalid instance or a genuinely-deleted row — never raises for those
    two cases, so both callers (`ensure_active_draft_with_demo_snapshot`,
    `attach_demo_snapshot`) can reject with the one fixed, generic
    `invalid_demo_selection` message regardless of which check failed.

    The query itself runs inside its own `transaction.atomic()` — a real
    database error there must propagate out of that block (never be
    swallowed here) so Django's own machinery rolls back to this block's
    savepoint *before* the exception reaches the caller. Both current
    callers already run this before their own `transaction.atomic()`
    write block and are themselves called from a `try`/`except` in
    `leads.demo_handoff` — so a real failure here is caught there, the
    caller's pending marker (if any) is restored, and the surrounding
    request transaction (e.g. login/registration under
    `ATOMIC_REQUESTS=True`) is left perfectly usable, exactly like the
    lookup in `leads.demo_handoff.consume_pending_demo_selection` itself.
    """
    if not isinstance(demo_selection, DemoSelection) or demo_selection.pk is None:
        return None
    with transaction.atomic():
        return DemoSelection.objects.select_related("template").filter(pk=demo_selection.pk).first()


def attach_demo_snapshot(*, owner, form_type, demo_selection):
    """Attach a frozen, bilingual snapshot of `demo_selection` to the
    owner's current active draft, and extend `expires_at` to exactly
    `DRAFT_RETENTION_DAYS` from now — attaching a snapshot is itself a
    valid draft-touching operation, exactly like `upsert_active_draft`.
    `fields`/`current_step` are left untouched.

    `demo_selection` must be a real, already saved `DemoSelection` row —
    never a dict, never raw JSON, never anything a caller could shape
    freely, and never trusted as the in-memory object handed in: it is
    re-read fresh from the database by primary key first, so a locally
    mutated instance (or one whose row has since been deleted) can never
    reach the snapshot builder. The snapshot itself is always produced by
    `build_demo_selection_snapshot` from that fresh copy (never
    caller-supplied) and is checked, value by value, against the exact
    expected shape before being written, so a draft can never end up
    holding a session_key/public_token/submission_token or any other
    unexpected or oversized structure.

    Session/ownership authorization of `demo_selection` (confirming it
    actually belongs to the request making this call) is the caller's
    responsibility in the phase that wires this up to a view — this
    service only guarantees the *shape* and *target* (the calling owner's
    own active draft) are safe.

    On any failure (invalid/deleted demo_selection, invalid snapshot
    shape, or no active draft to attach to), the previous draft — if any
    — is left completely untouched: nothing is written until the snapshot
    has been built and fully validated, and the "no active draft" case is
    only ever raised after the write transaction has already committed
    (see `_get_active_draft_locked`'s docstring for why that ordering
    matters for a concurrently-expiring draft).
    """
    _require_real_owner(owner)
    _require_supported_form_type(form_type)
    fresh_selection = _reload_demo_selection(demo_selection)
    if fresh_selection is None:
        _reject("invalid_demo_selection", "demo_selection must be a saved DemoSelection instance.")
    snapshot = build_demo_selection_snapshot(fresh_selection)
    _validate_snapshot_shape(snapshot)

    draft = None
    with transaction.atomic():
        locked_owner = owner.__class__.objects.select_for_update().get(pk=owner.pk)
        now = timezone.now()
        draft = _get_active_draft_locked(locked_owner, form_type, now)
        if draft is not None:
            draft.demo_snapshot = snapshot
            draft.expires_at = now + timedelta(days=DRAFT_RETENTION_DAYS)
            draft.save(update_fields=["demo_snapshot", "expires_at", "updated_at"])

    # Raised only after the transaction above has committed: if
    # _get_active_draft_locked just transitioned a stale draft to
    # "expired", that write must survive even though this function then
    # reports "no active draft" — raising it *inside* the atomic block
    # would roll that expiry back out along with everything else.
    if draft is None:
        _reject("no_active_draft", "No active draft exists to attach a snapshot to.")
    return draft


def clear_demo_snapshot(*, owner, form_type):
    """Explicitly clear the demo snapshot on the owner's current active
    draft and extend `expires_at` to exactly `DRAFT_RETENTION_DAYS` from
    now — clearing is itself a valid draft-touching operation, exactly
    like `upsert_active_draft`. `fields`/`current_step` are left
    untouched. This is the only other sanctioned way `demo_snapshot` may
    change after creation — ordinary field saves via `upsert_active_draft`
    never touch it, by design.
    """
    _require_real_owner(owner)
    _require_supported_form_type(form_type)

    draft = None
    with transaction.atomic():
        locked_owner = owner.__class__.objects.select_for_update().get(pk=owner.pk)
        now = timezone.now()
        draft = _get_active_draft_locked(locked_owner, form_type, now)
        if draft is not None:
            draft.demo_snapshot = {}
            draft.expires_at = now + timedelta(days=DRAFT_RETENTION_DAYS)
            draft.save(update_fields=["demo_snapshot", "expires_at", "updated_at"])

    # See attach_demo_snapshot: raised only after the transaction above
    # has committed, so a concurrently-discovered expiry is never rolled
    # back by this function's own "nothing to clear" outcome.
    if draft is None:
        _reject("no_active_draft", "No active draft exists to clear a snapshot from.")
    return draft


def delete_draft(owner, draft_id):
    """Hard-deletes a draft, strictly scoped to its own owner — a draft_id
    belonging to a different account is never touched, and this never
    raises for a nonexistent/foreign id; it just deletes nothing."""
    if owner is None or not getattr(owner, "is_authenticated", False):
        return False
    deleted, _ = FormDraft.objects.filter(pk=draft_id, owner=owner).delete()
    return deleted > 0
