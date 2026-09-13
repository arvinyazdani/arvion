"""Signal receivers bridging a pre-login demo selection into FormDraft.

Registered from `leads.apps.LeadsConfig.ready()` — deliberately kept out
of `accounts`, so that app stays fully decoupled from FormDraft/demo
selections; `accounts` only ever fires the stock `user_logged_in` signal
it already fires today, unaware of who else is listening.
"""

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .demo_handoff import consume_pending_demo_selection


@receiver(user_logged_in, dispatch_uid="leads.attach_pending_demo_selection_on_login")
def attach_pending_demo_selection_on_login(sender, request, user, **kwargs):
    """Consume a pending pre-login demo-selection marker (if any) right
    after a successful login/registration. All of the actual pop/fetch/
    attach/restore orchestration — and every bit of its error handling —
    lives in `leads.demo_handoff.consume_pending_demo_selection`, shared
    with the already-authenticated retry path on the contact page. This
    receiver is a thin trigger: it never raises, so it can never turn a
    successful login or registration into a failed one.
    """
    consume_pending_demo_selection(request, user)
