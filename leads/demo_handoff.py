"""Session-to-account hand-off for a visitor's demo selection.

Bridges `projects.DemoSelection` (anonymous, session-bound) into
`leads.FormDraft` (account-bound) across two paths:

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
   with a valid demo link — there is no login event to hook here, so the
   hand-off happens synchronously in the view instead.

Both paths write only through `leads.form_draft_service`'s sanctioned
functions — never a raw snapshot, never a live FK to `DemoSelection`.
Staff/superuser accounts are deliberately excluded from both paths: a
demo link opened while browsing as staff must never create or touch a
customer-shaped `FormDraft` owned by the staff account.
"""

import logging

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


def handle_resolved_demo_selection(request, selection):
    """Given a `selection` already validated by the caller's own
    session-bound lookup, either stash a pending marker (anonymous
    visitor, to be consumed on their next login) or sync it into the
    account's FormDraft immediately (already-authenticated, non-staff
    customer). Staff/superusers get neither: no marker is stored (nothing
    would ever consume it usefully) and no FormDraft is touched.

    Never raises: a rejection while syncing an already-authenticated
    customer's selection (e.g. a since-invalidated demo_selection) is
    logged and swallowed so the contact page still renders normally —
    this hand-off is a convenience, never a hard requirement for the page
    to work.
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
