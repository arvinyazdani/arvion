"""Signal receivers bridging a pre-login demo selection into FormDraft.

Registered from `leads.apps.LeadsConfig.ready()` — deliberately kept out
of `accounts`, so that app stays fully decoupled from FormDraft/demo
selections; `accounts` only ever fires the stock `user_logged_in` signal
it already fires today, unaware of who else is listening.
"""

import logging

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from projects.models import DemoSelection

from .demo_handoff import FORM_TYPE, pop_pending_demo_selection_id, store_pending_demo_selection
from .form_draft_service import DraftValidationError, ensure_active_draft_with_demo_snapshot

logger = logging.getLogger(__name__)


@receiver(user_logged_in, dispatch_uid="leads.attach_pending_demo_selection_on_login")
def attach_pending_demo_selection_on_login(sender, request, user, **kwargs):
    """Consume a pending pre-login demo-selection marker (if any) and
    attach its snapshot to the newly authenticated customer's FormDraft.

    Never blocks or fails the login/registration itself:
    - No marker, a malformed one, or one whose DemoSelection row no
      longer exists: silently does nothing (the marker is already gone —
      `pop_pending_demo_selection_id` always pops).
    - A definitive rejection while attaching (`DraftValidationError`,
      e.g. a same-instant deletion race) is logged and swallowed — this
      is a final outcome, not retried.
    - Anything else (a transient database error, etc.) is logged and the
      marker is restored so the customer's next authenticated request can
      retry, instead of silently losing the pending demo selection.

    The marker is popped *before* the staff/superuser check so a stray
    marker can never survive a staff login and later leak into a
    different, subsequent customer login on the same physical session.
    """
    selection_id = pop_pending_demo_selection_id(request)
    if selection_id is None:
        return
    if user.is_staff or user.is_superuser:
        return
    selection = DemoSelection.objects.select_related("template").filter(pk=selection_id).first()
    if selection is None:
        return
    try:
        ensure_active_draft_with_demo_snapshot(owner=user, form_type=FORM_TYPE, demo_selection=selection)
    except DraftValidationError:
        logger.warning("Rejected a pending demo selection while attaching it to a FormDraft after login.")
    except Exception:
        logger.exception("Unexpected error attaching a pending demo selection to a FormDraft after login.")
        store_pending_demo_selection(request, selection)
