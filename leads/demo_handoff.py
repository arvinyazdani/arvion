"""Session-to-account hand-off for a visitor's demo selection.

Bridges `projects.DemoSelection` (anonymous, session-bound) into
`leads.FormDraft` (account-bound) across three paths, all funnelling
into the single `consume_pending_demo_selection` orchestration below for
the marker-based ones:

1. An anonymous visitor picks a demo, then logs in or registers in the
   same browser tab. `django.contrib.auth.login()` rotates the session
   key immediately (`cycle_key()` for a previously-anonymous session,
   `flush()` — which wipes all session data — for one that already
   belonged to a *different* authenticated user), so nothing server-side
   can rely on the pre-login `?demo=` URL surviving past that point.
   Instead, a small, session-scoped marker holding only the
   `DemoSelection`'s internal numeric id (never its
   public_token/session_key/submission_token) is stored *before* login()
   runs, and consumed by `leads.signals.attach_pending_demo_selection_on_login`
   right after — `cycle_key()` preserves session data, so the marker
   survives; `flush()` destroys it, so it can never leak into a different
   account's login.
2. An already-authenticated, non-staff customer visits the contact page
   with a valid, explicit `?demo=` link — there is no login event to hook
   here, so the hand-off happens synchronously in the view instead
   (`handle_resolved_demo_selection`). A successful explicit attach here
   always supersedes and clears any stale pending marker.
3. The same customer visits the contact page again *without* a `?demo=`
   at all, and a pending marker from an earlier attempt (login-time or a
   prior visit) that failed transiently is still sitting in their
   session — `maybe_retry_pending_demo_selection` gives that marker
   exactly one more chance, scoped narrowly to this one page and this one
   precondition set so it never becomes a general middleware or an extra
   query on every page of the site.

All three write only through `leads.form_draft_service`'s sanctioned
functions — never a raw snapshot, never a live FK to `DemoSelection`.
Staff/superuser accounts are deliberately excluded from every path: a
demo link (or a lingering marker) must never create or touch a
customer-shaped `FormDraft` owned by a staff account.
"""

import logging

from django.db import transaction

from projects.models import DemoSelection

from .form_draft_service import DraftValidationError, ensure_active_draft_with_demo_snapshot

logger = logging.getLogger(__name__)

FORM_TYPE = "leads_contact"
PENDING_DEMO_SESSION_KEY = "leads:pending_demo_selection"


def store_pending_demo_selection(request, selection):
    """Record only `selection`'s internal numeric id and form_type in the
    current session — never its public_token/session_key/submission_token,
    and never the snapshot itself. Only ever called with a selection that
    has already been resolved through the view's own session-bound,
    token-matched lookup. Skips the write when the marker already holds
    the same value, so replaying the same `?demo=` link on an anonymous
    session does not keep dirtying (and re-saving) it on every request."""
    marker = {"demo_selection_id": selection.pk, "form_type": FORM_TYPE}
    if request.session.get(PENDING_DEMO_SESSION_KEY) != marker:
        request.session[PENDING_DEMO_SESSION_KEY] = marker


def _restore_pending_demo_selection_id(request, demo_selection_id):
    """Re-write the pending marker directly from an id already known to
    have come from a validated marker (via `pop_pending_demo_selection_id`)
    — used only to put a just-popped marker back after a presumed-
    transient failure, when fetching a full `DemoSelection` instance may
    itself be the very step that failed. Never accepts caller-supplied
    input from outside this module; not a general-purpose session writer."""
    if not isinstance(demo_selection_id, int) or isinstance(demo_selection_id, bool):
        return
    request.session[PENDING_DEMO_SESSION_KEY] = {"demo_selection_id": demo_selection_id, "form_type": FORM_TYPE}


def clear_pending_demo_selection(request):
    """Discard any pending marker outright — used after a successful
    explicit `?demo=` attach, since that supersedes whatever an older
    marker was pointing at and leaving it behind risks a later retry
    silently attaching unrelated, stale data."""
    request.session.pop(PENDING_DEMO_SESSION_KEY, None)


def pop_pending_demo_selection_id(request):
    """Remove and return the pending DemoSelection's internal id from this
    session, or None if the marker is absent, malformed, or not scoped to
    `FORM_TYPE`. Always pops — a malformed or foreign-form-type marker is
    discarded outright rather than left behind."""
    marker = request.session.pop(PENDING_DEMO_SESSION_KEY, None)
    if not isinstance(marker, dict) or marker.get("form_type") != FORM_TYPE:
        return None
    selection_id = marker.get("demo_selection_id")
    if not isinstance(selection_id, int) or isinstance(selection_id, bool):
        return None
    return selection_id


def consume_pending_demo_selection(request, user):
    """The single safe orchestration for turning a pending marker into an
    attached FormDraft snapshot. Shared by the post-login signal receiver
    and the already-authenticated retry path on the contact page — both
    fire the exact same pop/staff-check/fetch/attach/restore sequence;
    only what *triggers* the call differs.

    Never raises, under any failure mode:
    - No marker, a malformed one, or one scoped to a different form_type:
      does nothing (`pop_pending_demo_selection_id` already discarded it).
    - A staff/superuser account: does nothing (the marker was already
      popped above, so it can never survive into a later, different
      customer's login on the same physical session).
    - The `DemoSelection` row genuinely no longer exists: does nothing
      (a final, non-retryable outcome — the marker stays discarded).
    - The `DemoSelection` lookup itself raises (a transient database
      error, etc.): logs a fixed message and restores the marker (by id
      only — the row was never actually fetched) so a later attempt can
      retry; no partial or corrupt `FormDraft` is ever created. The
      lookup runs inside its own `transaction.atomic()` block, and the
      `try`/`except` around it sits *outside* that block — under
      `ATOMIC_REQUESTS=True`, a genuine database error there aborts the
      underlying PostgreSQL transaction; only letting the exception
      propagate out of `atomic()` first makes Django roll back to that
      block's own savepoint before we catch it, leaving the *outer*
      request transaction (login/registration) clean and still usable.
      Catching the exception *inside* the `atomic()` block instead would
      swallow it before `atomic()` ever sees a failure to roll back from,
      leaving the outer transaction's connection still marked as needing
      a rollback — the next query in the same request would then fail
      with `TransactionManagementError`, or the whole request would be
      forced to roll back regardless of what this function did.
    - `ensure_active_draft_with_demo_snapshot` raises `DraftValidationError`
      (a definitive rejection, e.g. a same-instant deletion race or an
      invalid snapshot shape): logs a fixed message and does not restore
      the marker — this outcome will not change on retry.
    - `ensure_active_draft_with_demo_snapshot` raises anything else (a
      transient database error, etc.): logs a fixed message and restores
      the marker for a later retry.

    No log message here ever includes a token, session key, id, or any
    other payload value — every message is a fixed string.
    """
    selection_id = pop_pending_demo_selection_id(request)
    if selection_id is None:
        return
    if user.is_staff or user.is_superuser:
        return

    try:
        with transaction.atomic():
            selection = DemoSelection.objects.select_related("template").filter(pk=selection_id).first()
    except Exception:
        # The `except` deliberately sits outside the `atomic()` block
        # above: an exception raised *inside* it makes `atomic()` roll
        # back to its own savepoint before propagating here, so the
        # surrounding request transaction (e.g. login/registration under
        # ATOMIC_REQUESTS) is never left needing a rollback of its own.
        logger.exception("Unexpected error looking up a pending demo selection.")
        _restore_pending_demo_selection_id(request, selection_id)
        return
    if selection is None:
        return

    try:
        ensure_active_draft_with_demo_snapshot(owner=user, form_type=FORM_TYPE, demo_selection=selection)
    except DraftValidationError:
        logger.warning("Rejected a pending demo selection while attaching it to a FormDraft.")
    except Exception:
        logger.exception("Unexpected error attaching a pending demo selection to a FormDraft.")
        _restore_pending_demo_selection_id(request, selection_id)


def handle_resolved_demo_selection(request, selection):
    """Given a `selection` already validated by the caller's own
    session-bound lookup (an explicit, valid `?demo=` in the URL — this
    always takes precedence over any stale pending marker), either stash
    a pending marker (anonymous visitor, to be consumed on their next
    login) or sync it into the account's FormDraft immediately
    (already-authenticated, non-staff customer). Staff/superusers get
    neither: no marker is stored (nothing would ever consume it usefully)
    and no FormDraft is touched.

    Never raises: a `DraftValidationError` (a definitive rejection, e.g.
    a since-invalidated demo_selection) or any other exception (a
    transient database error, etc.) while syncing an already-
    authenticated customer's selection is logged and swallowed so the
    contact page always still renders normally — this hand-off is a
    convenience, never a hard requirement for the page to work.
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        store_pending_demo_selection(request, selection)
        return
    if user.is_staff or user.is_superuser:
        return
    try:
        ensure_active_draft_with_demo_snapshot(owner=user, form_type=FORM_TYPE, demo_selection=selection)
    except DraftValidationError:
        logger.warning(
            "Rejected an already-authenticated customer's demo selection while syncing it to a FormDraft."
        )
        return
    except Exception:
        logger.exception(
            "Unexpected error syncing an already-authenticated customer's demo selection to a FormDraft."
        )
        return
    # The explicit demo just won and was attached successfully — an older
    # pending marker (from an earlier failed attempt, or an unrelated
    # session-key-bound selection) must not linger and get retried later.
    clear_pending_demo_selection(request)


def maybe_retry_pending_demo_selection(request):
    """Retry path for the one specific, narrow case this hand-off can
    otherwise permanently lose a pending demo selection: an
    already-authenticated, non-staff customer's *previous* attempt to
    attach it (at login, or an earlier visit to this same page) hit a
    transient error and the marker survived for a retry.

    Deliberately scoped to exactly one page (the contact page, via its
    own explicit call site) and one precondition set — this must never
    become a general middleware or an extra query on every page of the
    site:
    - the request has no `?demo=` at all — an explicit, valid demo link
      always wins instead (see `handle_resolved_demo_selection`), and an
      explicit but invalid/foreign one intentionally does *not* fall back
      to retrying an old marker, so a wrong link can never silently
      resurrect unrelated stale data; the caller is responsible for this
      check (only calling here when there was no resolved selection *and*
      no `demo` query parameter at all)
    - the visitor is authenticated and not staff/superuser
    - a pending marker actually exists in this session (a plain
      in-session key check — no query — so a visitor who never triggered
      the hand-off pays no extra cost at all)

    Consuming it is delegated to `consume_pending_demo_selection`, the
    exact same orchestration the login-time receiver uses, so first
    attempt and retry share one code path and one set of error/restore
    semantics.
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated or user.is_staff or user.is_superuser:
        return
    if PENDING_DEMO_SESSION_KEY not in request.session:
        return
    consume_pending_demo_selection(request, user)
