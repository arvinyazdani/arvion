"""The only sanctioned way to create, read, update, expire, or delete a
`FormDraft`. Nothing outside this module should construct or save one
directly — this is where the field allowlist, the race-safe single-active-
draft rule, the expiry lifecycle, and the demo-snapshot attach/clear rules
are enforced.

Scope: leads_contact only. `leads.signals` (pre-login hand-off),
`leads.views.contact.LeadCreateView` (already-authenticated hand-off, and
— via `finalize_form_draft_to_lead` — the final, account-bound submission
path), and `leads.views.draft_api` (the account-bound read/save/delete
API) are the only callers outside this module and its own tests.

Every `DraftValidationError` message below is a fixed, generic string with
no interpolated value or caller-supplied key name: both a submitted field
value and an unrecognized field's own name may be attacker-controlled, and
this module's exceptions are allowed to reach logs, admin error pages, or
API responses. Categorization is via the `.code` attribute, drawn only
from this module's own fixed vocabulary — never from payload content.

`FormDraft.revision` is this module's optimistic-concurrency counter: it
starts at 1 on creation and increments by exactly 1 whenever `fields`/
`current_step`/`demo_snapshot`/`status` actually change (an idempotent
no-op save never bumps it, though it may still extend `expires_at`).
`save_draft_fields`/`delete_draft_with_revision` are the only functions
that take a caller-supplied `expected_revision` and enforce it, raising
`DraftConflictError` (carrying the current, canonical draft) on a
mismatch — every other write function in this module changes `revision`
unconditionally as a side effect of a real content change, with no
precondition check of its own.
"""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
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
_DEMO_SNAPSHOT_BRIEF_KEYS = frozenset(("brief_fa", "brief_en"))
_MAX_SNAPSHOT_TEXT_LENGTH = 300
_MAX_SNAPSHOT_FEATURE_LENGTH = 200
_MAX_SNAPSHOT_FEATURE_COUNT = 20


class DraftValidationError(ValidationError):
    """Raised for an invalid owner, form_type, current_step, field, or
    demo_selection. See the module docstring: messages never repeat
    caller-supplied content."""


class DraftConflictError(Exception):
    """Raised by `save_draft_fields`/`delete_draft_with_revision` when a
    caller's `expected_revision` does not match the draft's actual
    current revision (including the case where the caller expected a
    draft to exist — any `expected_revision != 0` — but none does, or
    vice versa). Carries the current, canonical draft as `.draft` (or
    `None` when none exists) so the caller can build a 409 response
    without a second query — `.draft`, when not `None`, always belongs to
    the exact same owner who made the request; this error is never
    raised with, and never exposes, another account's data. The message
    is fixed and never repeats any caller-supplied value."""

    def __init__(self, draft):
        self.draft = draft
        super().__init__("The draft has changed since it was last read.")


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


def _require_non_staff_owner(owner):
    """Defense in depth for the account-bound draft API: the view is the
    primary place staff/superuser accounts are turned away (with a 403,
    before any query), but any other caller of `save_draft_fields`/
    `delete_draft_with_revision` — direct, future, or in tests — gets the
    same guarantee. A staff/superuser account must never create or modify
    a customer-shaped `FormDraft` of its own."""
    if owner.is_staff or owner.is_superuser:
        _reject("staff_or_superuser_not_allowed", "Staff and superuser accounts cannot own a customer draft.")


def _validate_expected_revision(expected_revision):
    if not isinstance(expected_revision, int) or isinstance(expected_revision, bool) or expected_revision < 0:
        _reject("invalid_expected_revision", "expected_revision must be a non-negative integer.")


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
    if not isinstance(snapshot, dict) or set(snapshot) not in (
        _DEMO_SNAPSHOT_ALLOWED_KEYS,
        _DEMO_SNAPSHOT_ALLOWED_KEYS | _DEMO_SNAPSHOT_BRIEF_KEYS,
    ):
        _reject("invalid_snapshot_shape", "Demo snapshot has an unexpected shape.")
    for key in _DEMO_SNAPSHOT_TEXT_KEYS:
        if not _is_safe_snapshot_string(snapshot[key]):
            _reject("invalid_snapshot_shape", "Demo snapshot has an unexpected shape.")
    for key in _DEMO_SNAPSHOT_FEATURE_KEYS:
        if not _is_safe_feature_list(snapshot[key]):
            _reject("invalid_snapshot_shape", "Demo snapshot has an unexpected shape.")
    if len(snapshot["features_fa"]) != len(snapshot["features_en"]):
        _reject("invalid_snapshot_shape", "Demo snapshot has an unexpected shape.")
    if "brief_fa" in snapshot:
        for key in _DEMO_SNAPSHOT_BRIEF_KEYS:
            rows = snapshot[key]
            if not isinstance(rows, list) or not 1 <= len(rows) <= 4:
                _reject("invalid_snapshot_shape", "Demo snapshot has an unexpected shape.")
            for row in rows:
                if (not isinstance(row, dict) or set(row) != {"label", "value"}
                        or not all(_is_safe_snapshot_string(value) for value in row.values())):
                    _reject("invalid_snapshot_shape", "Demo snapshot has an unexpected shape.")
        if len(snapshot["brief_fa"]) != len(snapshot["brief_en"]):
            _reject("invalid_snapshot_shape", "Demo snapshot has an unexpected shape.")


def _get_active_draft_locked(locked_owner, form_type, now):
    """Must only be called with `locked_owner` already `select_for_update()`-
    locked inside an open transaction. The only place an active draft's
    status is ever transitioned to "expired" as a write: everywhere else
    (get_active_draft) is read-only. A status change is itself a real
    content change, so it bumps `revision` exactly like any other write
    below — a client polling with a stale `expected_revision` against a
    row that expired between reads must see a conflict, not a silent
    stale match."""
    existing = FormDraft.objects.filter(
        owner=locked_owner, form_type=form_type, status__in=FormDraft.ACTIVE_STATUSES,
    ).first()
    if existing and existing.expires_at <= now:
        existing.status = "expired"
        existing.revision = existing.revision + 1
        existing.save(update_fields=["status", "revision", "updated_at"])
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
    valid save. `revision` increments by exactly 1 only when `fields`/
    `current_step` actually change — a byte-identical save extends
    `expires_at` but never bumps it.

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
            changed = existing.fields != cleaned_fields or existing.current_step != current_step
            existing.current_step = current_step
            existing.fields = cleaned_fields
            existing.expires_at = expires_at
            update_fields = ["current_step", "fields", "expires_at", "updated_at"]
            if changed:
                existing.revision = existing.revision + 1
                update_fields.append("revision")
            existing.save(update_fields=update_fields)
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
    are left untouched, exactly like `attach_demo_snapshot`. `revision`
    increments by exactly 1 only when the snapshot's actual content
    changes on an existing draft — attaching the identical snapshot again
    still extends `expires_at` but never bumps it.

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
        changed = existing.demo_snapshot != snapshot
        existing.demo_snapshot = snapshot
        existing.expires_at = expires_at
        update_fields = ["demo_snapshot", "expires_at", "updated_at"]
        if changed:
            existing.revision = existing.revision + 1
            update_fields.append("revision")
        existing.save(update_fields=update_fields)
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
    `fields`/`current_step` are left untouched. `revision` increments by
    exactly 1 only when the snapshot's actual content changes — attaching
    the identical snapshot again still extends `expires_at` but never
    bumps it.

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
            changed = draft.demo_snapshot != snapshot
            draft.demo_snapshot = snapshot
            draft.expires_at = now + timedelta(days=DRAFT_RETENTION_DAYS)
            update_fields = ["demo_snapshot", "expires_at", "updated_at"]
            if changed:
                draft.revision = draft.revision + 1
                update_fields.append("revision")
            draft.save(update_fields=update_fields)

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
    never touch it, by design. `revision` increments by exactly 1 only
    when there was actually something to clear — clearing an
    already-empty snapshot still extends `expires_at` but never bumps it.
    """
    _require_real_owner(owner)
    _require_supported_form_type(form_type)

    draft = None
    with transaction.atomic():
        locked_owner = owner.__class__.objects.select_for_update().get(pk=owner.pk)
        now = timezone.now()
        draft = _get_active_draft_locked(locked_owner, form_type, now)
        if draft is not None:
            changed = draft.demo_snapshot != {}
            draft.demo_snapshot = {}
            draft.expires_at = now + timedelta(days=DRAFT_RETENTION_DAYS)
            update_fields = ["demo_snapshot", "expires_at", "updated_at"]
            if changed:
                draft.revision = draft.revision + 1
                update_fields.append("revision")
            draft.save(update_fields=update_fields)

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


_NO_CONFLICT = object()


def save_draft_fields(*, owner, form_type, fields, current_step, expected_revision):
    """The race-safe, revision-checked create-or-update behind the
    account-bound draft API (`leads.views.draft_api`). Unlike
    `upsert_active_draft`, this enforces optimistic concurrency: the
    caller must supply the revision they last observed —
    `expected_revision=0` means "I believe no active draft exists yet."

    On a mismatch, raises `DraftConflictError` carrying the current,
    canonical draft (or `None` if none exists) — nothing is written.
    This includes the case where `existing is None` but
    `expected_revision != 0`: the caller's belief that a draft (of some
    revision) already existed is itself already stale, so it is treated
    as a conflict rather than silently creating a new draft with a
    surprising revision.

    On success, returns `(draft, created)`. Never touches `demo_snapshot`
    — only `attach_demo_snapshot`/`clear_demo_snapshot`/
    `ensure_active_draft_with_demo_snapshot` may change it. Idempotent:
    resaving a payload identical to the existing `fields`/`current_step`
    still extends `expires_at` but never bumps `revision` — see
    `upsert_active_draft`'s docstring for the same rule.

    Staff/superuser accounts are rejected outright (defense in depth —
    the view itself already turns them away with a 403 before ever
    calling this).

    `DraftConflictError` is only ever raised *after* the write
    transaction below has committed, never from inside it — exactly like
    `attach_demo_snapshot`/`clear_demo_snapshot`'s own `no_active_draft`
    case. `_get_active_draft_locked` may itself transition a stale draft
    to `"expired"` (bumping its `revision`) as part of finding "the"
    active draft; if `expected_revision` then turns out not to match
    (including the `existing is None` "the draft is gone" case), raising
    the conflict from *inside* the same `transaction.atomic()` block
    would roll that expiry transition back out along with everything
    else — an exception propagating out of `atomic()` undoes the whole
    block, including writes that have nothing to do with why the
    exception was raised. The conflict outcome is instead recorded in a
    local sentinel and only turned into a raised `DraftConflictError`
    once the `with` block has exited normally, so the expiry transition
    always survives regardless of whether this call goes on to report a
    conflict.
    """
    _require_real_owner(owner)
    _require_non_staff_owner(owner)
    _require_supported_form_type(form_type)
    _validate_current_step(form_type, current_step)
    _validate_expected_revision(expected_revision)
    cleaned_fields = normalize_fields(form_type, fields)

    conflict = _NO_CONFLICT
    draft = None
    created = False

    with transaction.atomic():
        locked_owner = owner.__class__.objects.select_for_update().get(pk=owner.pk)
        now = timezone.now()
        existing = _get_active_draft_locked(locked_owner, form_type, now)
        expires_at = now + timedelta(days=DRAFT_RETENTION_DAYS)

        if existing is None:
            if expected_revision != 0:
                # No active draft exists (never did, or just expired
                # above) — that in itself is the conflict; report it as
                # "canonical: none" rather than silently creating a new
                # draft with a surprising revision.
                conflict = None
            else:
                draft = FormDraft.objects.create(
                    owner=locked_owner, form_type=form_type, current_step=current_step,
                    fields=cleaned_fields, expires_at=expires_at,
                )
                created = True
        elif existing.revision != expected_revision:
            conflict = existing
        else:
            changed = existing.fields != cleaned_fields or existing.current_step != current_step
            existing.current_step = current_step
            existing.fields = cleaned_fields
            existing.expires_at = expires_at
            update_fields = ["current_step", "fields", "expires_at", "updated_at"]
            if changed:
                existing.revision = existing.revision + 1
                update_fields.append("revision")
            existing.save(update_fields=update_fields)
            draft = existing

    if conflict is not _NO_CONFLICT:
        raise DraftConflictError(conflict)
    return draft, created


def delete_draft_with_revision(*, owner, form_type, expected_revision):
    """Hard-deletes the owner's active draft for `form_type`, enforcing
    the same optimistic-concurrency contract as `save_draft_fields`.

    Idempotent when no active draft exists: returns `False` without
    raising and without regard to `expected_revision` (there is nothing
    to conflict with). Strictly ownership-scoped by construction — the
    row is found via the owner's own lock and this form_type only; no
    draft id is ever accepted from a caller, so there is no id a client
    could pass to reach another account's draft.

    On a revision mismatch (an active draft does exist, but not at the
    expected revision), raises `DraftConflictError` carrying the current,
    canonical draft — nothing is deleted.
    """
    _require_real_owner(owner)
    _require_non_staff_owner(owner)
    _require_supported_form_type(form_type)
    _validate_expected_revision(expected_revision)

    with transaction.atomic():
        locked_owner = owner.__class__.objects.select_for_update().get(pk=owner.pk)
        now = timezone.now()
        existing = _get_active_draft_locked(locked_owner, form_type, now)
        if existing is None:
            return False
        if existing.revision != expected_revision:
            raise DraftConflictError(existing)
        existing.delete()
        return True


FINALIZE_FORM_TYPE = "leads_contact"
MAX_SUBMISSION_TOKEN_LENGTH = 64


class FinalizeSubmissionError(Exception):
    """Base class for every rejection `finalize_form_draft_to_lead` can
    raise. Every message is a fixed, generic string — never a
    caller-supplied value, never the token itself — safe to reach a log,
    an admin error page, or a bilingual view-level message. See each
    subclass's own docstring for exactly what it represents."""


class InvalidSubmissionTokenError(FinalizeSubmissionError):
    """A missing, empty, or too-long `final_submission_token` — and,
    deliberately, also a token that belongs to a different owner (see
    `ForeignSubmissionTokenError`, which this class effectively merges
    with at the call site): the two are never told apart in what a caller
    can observe, since doing so would let a caller learn whether a given
    token string exists at all."""


class ForeignSubmissionTokenError(InvalidSubmissionTokenError):
    """`final_submission_token` names a real `FormDraft` row, but not one
    belonging to the requesting owner. Subclasses
    `InvalidSubmissionTokenError` on purpose — callers that only catch the
    parent already reject this exactly like a malformed token, with the
    same fixed message; nothing distinguishes "belongs to someone else"
    from "not a real token" anywhere a caller could observe it."""


class NewLeadRateLimitedError(FinalizeSubmissionError):
    """Raised only on the genuinely-new-Lead path, only when the caller's
    own `allow_new_lead()` callable returns `False`. Never raised on a
    replay — replaying an already-completed submission is never
    rate-limited, regardless of how recently a new Lead was created from
    the same IP."""


class SubmissionConflictError(FinalizeSubmissionError):
    """`final_submission_token` names a `FormDraft` whose `submitted_lead`
    already exists, but this submission's canonical content differs from
    that Lead's own current, stored values. Never silently treated as a
    replay, and the original Lead is left completely untouched — the
    caller must show a safe, bilingual conflict message instead."""


def _validate_submission_token(raw_token):
    token = (raw_token or "").strip()
    if not token or len(token) > MAX_SUBMISSION_TOKEN_LENGTH:
        _raise_invalid_submission_token()
    return token


def _raise_invalid_submission_token():
    raise InvalidSubmissionTokenError("The submission token is missing or invalid.")


def _minimal_draft_fields_from_cleaned_data(cleaned_data):
    """The exact same five-field allowlist every other draft-writing
    function in this module enforces, extracted from the already-validated
    final form — used only for the one case where no autosave ever created
    a draft before the customer reached Submit. Reuses `normalize_fields`
    itself, so this can never silently diverge from the allowlist enforced
    everywhere else in this module."""
    service = cleaned_data.get("service")
    raw = {
        "request_type": cleaned_data.get("request_type"),
        "budget_range": cleaned_data.get("budget_range"),
        "timeline": cleaned_data.get("timeline"),
        "preferred_contact": cleaned_data.get("preferred_contact"),
    }
    if service is not None:
        raw["service_id"] = service.pk
    return normalize_fields(FINALIZE_FORM_TYPE, raw)


def _lead_canonical_signature(lead):
    """Every field a replay must match, byte for byte, against the
    already-created Lead — service and other nullable/FK values are
    compared in their normalized, stored form (never re-derived from a
    caller-supplied guess), exactly like `phone`, which `LeadForm.
    clean_phone` already normalizes before it is ever saved. Includes
    `demo_selection_id`: two submissions with identical form content but a
    different (or added, or removed) demo selection are different
    submissions, not a replay of each other."""
    return {
        "request_type": lead.request_type,
        "service_id": lead.service_id,
        "budget_range": lead.budget_range,
        "timeline": lead.timeline,
        "preferred_contact": lead.preferred_contact,
        "name": lead.name,
        "business_name": lead.business_name or "",
        "email_or_telegram": lead.email_or_telegram,
        "phone": lead.phone or "",
        "website_url": lead.website_url or "",
        "message": lead.message,
        "demo_selection_id": lead.demo_selection_id,
    }


def _submission_canonical_signature(cleaned_data, demo_selection):
    """The same shape as `_lead_canonical_signature`, built from this exact
    request's own inputs: the just-validated form and the caller's already
    resolved, session-bound `demo_selection` (never a `DemoSelection`
    reconstructed from a draft's frozen `demo_snapshot`, which could go
    stale independently of the live row)."""
    service = cleaned_data.get("service")
    return {
        "request_type": cleaned_data.get("request_type"),
        "service_id": service.pk if service else None,
        "budget_range": cleaned_data.get("budget_range"),
        "timeline": cleaned_data.get("timeline"),
        "preferred_contact": cleaned_data.get("preferred_contact"),
        "name": cleaned_data.get("name", ""),
        "business_name": cleaned_data.get("business_name") or "",
        "email_or_telegram": cleaned_data.get("email_or_telegram", ""),
        "phone": cleaned_data.get("phone") or "",
        "website_url": cleaned_data.get("website_url") or "",
        "message": cleaned_data.get("message", ""),
        "demo_selection_id": demo_selection.pk if demo_selection is not None else None,
    }


def _lead_matches_this_submission(lead, cleaned_data, demo_selection):
    return _lead_canonical_signature(lead) == _submission_canonical_signature(cleaned_data, demo_selection)


def finalize_form_draft_to_lead(*, owner, form, final_submission_token, demo_selection, allow_new_lead, on_created=None, use_saved_demo_snapshot=True):
    """The only sanctioned way to convert a customer's `leads_contact`
    `FormDraft` into a `Lead`, atomically and without ever creating a
    duplicate `Lead` for the same submission attempt. Called only from
    `LeadCreateView.form_valid()`, only for an authenticated, non-staff,
    non-superuser customer. `form` must already be a validated `LeadForm`
    (`form.is_valid()` already `True`) — this never validates form fields
    itself, only the draft/token/ownership/rate-limit state around it, and
    it never lets `FormDraft` data override anything `form.cleaned_data`
    already holds: the validated POST is the sole source of every `Lead`
    field.

    `final_submission_token` is the raw value read from the POST body's
    hidden `final_submission_token` field — a fresh, server-minted,
    non-secret idempotency key rendered on every ordinary `GET` of the
    contact page for an authenticated non-staff customer (never on a
    validation-error rerender, which instead echoes back the token the
    customer already submitted, so a fix-and-retry is still recognized as
    the same attempt — see `LeadCreateView._resolved_final_submission_token`).

    `demo_selection` is the caller's already-resolved, session-bound
    `DemoSelection` (or `None`) — resolved and authorized exactly the same
    way the pre-existing guest/staff/superuser path already does; this
    function never derives a live FK from a draft's frozen `demo_snapshot`.
    When no live selection exists, `use_saved_demo_snapshot` preserves the
    owner's validated frozen choice on the Lead's case in this transaction.
    The caller disables that fallback for an explicit unresolved demo link.

    `allow_new_lead` is a zero-argument callable the caller supplies
    (normally wrapping its own IP-based rate limiter). It is called, and
    its return value enforced, only on the path that is about to create a
    genuinely new `Lead` — a replay of an already-completed submission
    never consults it and is never rate-limited.

    `on_created`, if given, is called with the new `Lead` via
    `transaction.on_commit()` from *inside* this function's own open
    transaction — so it only ever runs after a real, successful commit,
    exactly once, and never at all on a replay or on any rollback. The
    caller is expected to pass a closure that sends the notification email
    (kept out of this module so it stays decoupled from Django's mail
    backend and independently testable).

    Returns `(lead, created)` — `created` is `True` only when this call
    itself just made a new `Lead`; `False` for a recognized replay of an
    already-completed submission (same token, same canonical content —
    `lead` is the original `Lead`; nothing was written).

    Raises `InvalidSubmissionTokenError` (covers a missing/malformed
    token, one belonging to a different owner found at the initial
    lookup, and one that resolves to a different owner after a real
    unique-constraint collision is recovered from — none of these are
    ever distinguished in what is raised), `NewLeadRateLimitedError`
    (this would have been a new `Lead`, and the caller's own rate limiter
    refused it), or `SubmissionConflictError` (the token already names a
    completed `Lead` whose content — including its `demo_selection` —
    differs from this submission's, or names an untrusted, never-
    submitted record recovered from a unique-constraint collision).
    """
    _require_real_owner(owner)
    _require_non_staff_owner(owner)
    token = _validate_submission_token(final_submission_token)

    lead = None
    created = False

    with transaction.atomic():
        locked_owner = owner.__class__.objects.select_for_update().get(pk=owner.pk)
        # Re-checked against the freshest, lock-held row: request.user may
        # be a stale copy of the account from before this exact request if
        # anything about it changed between session authentication and
        # this query.
        if locked_owner.is_staff or locked_owner.is_superuser or not locked_owner.is_active:
            _raise_invalid_submission_token()

        existing = FormDraft.objects.filter(submission_token=token).first()
        if existing is not None:
            if existing.owner_id != locked_owner.pk or existing.form_type != FINALIZE_FORM_TYPE:
                # Never reveal whether the token exists at all — identical
                # outward behavior to a token that was never issued.
                raise ForeignSubmissionTokenError("The submission token is missing or invalid.")
            if existing.submitted_lead_id is not None:
                original = existing.submitted_lead
                if _lead_matches_this_submission(original, form.cleaned_data, demo_selection):
                    return original, False
                raise SubmissionConflictError(
                    "This submission was already recorded with different information."
                )
            # A token attached to a not-yet-submitted draft, owned by this
            # same locked owner, can only be a leftover from an attempt
            # that never reached "submitted" — the owner-row lock this
            # function itself holds for its entire duration means no other
            # request for this owner can be concurrently mid-flight right
            # now, and the transition below always commits the
            # "submitting" write and the "submitted" write together, in
            # the same outer transaction (never one without the other) —
            # so this state, reached under a fresh lock, is safe to resume
            # rather than treat as a conflict.
            draft = existing
        else:
            now = timezone.now()
            draft = _get_active_draft_locked(locked_owner, FINALIZE_FORM_TYPE, now)
            creating = draft is None
            minimal_fields = _minimal_draft_fields_from_cleaned_data(form.cleaned_data) if creating else None
            try:
                with transaction.atomic():
                    if creating:
                        draft = FormDraft.objects.create(
                            owner=locked_owner, form_type=FINALIZE_FORM_TYPE, fields=minimal_fields,
                            current_step=FORM_TYPE_STEP_COUNTS[FINALIZE_FORM_TYPE] - 1, status="submitting",
                            submission_token=token, expires_at=now + timedelta(days=DRAFT_RETENTION_DAYS),
                        )
                    else:
                        draft.status = "submitting"
                        draft.submission_token = token
                        draft.revision = draft.revision + 1
                        draft.save(update_fields=["status", "submission_token", "revision", "updated_at"])
            except IntegrityError:
                # Last line of defense against a token collision — the
                # owner-row lock above already makes this unreachable for
                # a same-owner race, so in practice this only guards a
                # (cryptographically negligible) cross-owner token
                # collision, or a future change that weakens the lock.
                # Re-read scoped by owner+form_type, never by token alone,
                # and never guess: only a matching, already-completed
                # submission for this exact owner is treated as a replay.
                recovered = FormDraft.objects.filter(
                    owner=locked_owner, form_type=FINALIZE_FORM_TYPE, submission_token=token,
                ).first()
                if recovered is None:
                    # Nothing for *this* owner claimed the token — the row
                    # that actually won the unique constraint belongs to
                    # someone else. Identical outward behavior to a token
                    # that was never issued or that names a different
                    # owner: never reveal that a collision happened at all.
                    _raise_invalid_submission_token()
                if recovered.submitted_lead_id is None:
                    # A record exists for this owner+token but never
                    # reached "submitted" — under the owner-row lock this
                    # should be unreachable, so it is not trusted as a
                    # resumable draft; a safe rejection that creates
                    # nothing is the only sound response.
                    raise SubmissionConflictError(
                        "This submission was already recorded with different information."
                    )
                original = recovered.submitted_lead
                if _lead_matches_this_submission(original, form.cleaned_data, demo_selection):
                    return original, False
                raise SubmissionConflictError(
                    "This submission was already recorded with different information."
                )

        if not allow_new_lead():
            raise NewLeadRateLimitedError("Please wait before submitting another enquiry.")

        lead = form.save(commit=False)
        if demo_selection is not None:
            lead.demo_selection = demo_selection
        lead.privacy_accepted_at = timezone.now()
        lead.save()
        if demo_selection is None and use_saved_demo_snapshot and draft.demo_snapshot:
            # Cross-device continuation has an authorized frozen snapshot,
            # not a session-bound live FK. Preserve it on this new Lead's
            # case inside the same transaction; never reconstruct the FK.
            _validate_snapshot_shape(draft.demo_snapshot)
            from management_portal.cases import sync_demo_snapshot_document
            from management_portal.models import CustomerCase
            case = CustomerCase.objects.get(kind="lead", source_object_id=lead.pk)
            sync_demo_snapshot_document(case, lead, draft.demo_snapshot)
        created = True

        draft.submitted_lead = lead
        draft.status = "submitted"
        draft.revision = draft.revision + 1
        draft.save(update_fields=["submitted_lead", "status", "revision", "updated_at"])

        if on_created is not None:
            transaction.on_commit(lambda: on_created(lead))

    return lead, created


def serialize_draft_canonical(draft):
    """The only safe, external representation of a `FormDraft` — used by
    every response the account-bound draft API ever returns, success or
    conflict alike, so a client never sees two different shapes for "the
    current state of my draft." Never includes the database primary key,
    `owner_id`, `submitted_lead_id`, or any token/session key — only the
    fields a client legitimately needs to render and resume its own
    draft, and to detect and resolve a revision conflict."""
    return {
        "form_type": draft.form_type,
        "current_step": draft.current_step,
        "fields": draft.fields,
        "demo_snapshot": draft.demo_snapshot,
        "status": draft.status,
        "revision": draft.revision,
        "updated_at": draft.updated_at.isoformat(),
        "expires_at": draft.expires_at.isoformat(),
    }
