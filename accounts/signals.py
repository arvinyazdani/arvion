import hashlib
import hmac

from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.db import transaction
from django.dispatch import receiver

from .models import ActiveSession, User

# Only for the courtesy message shown on a stale session's next request —
# never the security boundary itself, which is the immediate Session
# deletion below. A day is generous; the marker is consumed (deleted) the
# first time it is read, so its lifetime only bounds how long a visitor who
# never returns could theoretically still see the notice.
SESSION_INVALIDATION_MARKER_TIMEOUT = 60 * 60 * 24


def is_single_session_enforced(user):
    """Ordinary customer accounts only — staff/superusers may hold several
    concurrent sessions (public site + management portal), and the whole
    rule can be disabled via SINGLE_SESSION_ENFORCED without a code change."""
    return bool(settings.SINGLE_SESSION_ENFORCED) and not user.is_staff and not user.is_superuser


def session_invalidation_marker_key(session_key):
    """A keyed, irreversible digest — never the raw session key itself —
    used only as a cache lookup key for the one-time courtesy message."""
    digest = hmac.new(settings.SECRET_KEY.encode(), session_key.encode(), hashlib.sha256).hexdigest()
    return f"single-session-invalidated:{digest}"


@receiver(user_logged_in, dispatch_uid="accounts.enforce_single_session_on_login")
def enforce_single_session_on_login(sender, request, user, **kwargs):
    if not is_single_session_enforced(user):
        return
    if not request.session.session_key:
        # login() takes one of two paths: a fresh/matching session gets
        # cycle_key(), which mints a key immediately — but a session that
        # was authenticated as a *different* user gets flush() instead,
        # which clears the key without creating a new one on the spot (only
        # SessionMiddleware's later process_response() would, via .save());
        # by then this receiver has already run. Force it now so a real key
        # always exists before we read it below.
        request.session.save()
    new_key = request.session.session_key
    if not new_key:
        return
    with transaction.atomic():
        locked_user = User.objects.select_for_update().get(pk=user.pk)
        active, created = ActiveSession.objects.select_for_update().get_or_create(
            user=locked_user, defaults={"session_key": new_key},
        )
        old_key = active.session_key
        if not created and old_key != new_key:
            try:
                cache.set(session_invalidation_marker_key(old_key), True, SESSION_INVALIDATION_MARKER_TIMEOUT)
            except Exception:
                pass
            Session.objects.filter(session_key=old_key).delete()
            active.session_key = new_key
            active.save(update_fields=["session_key", "updated_at"])


@receiver(user_logged_out, dispatch_uid="accounts.release_active_session_on_logout")
def release_active_session_on_logout(sender, request, user, **kwargs):
    if user is None or not user.is_authenticated:
        return
    session_key = getattr(request.session, "session_key", None)
    if not session_key:
        return
    # Matches on the exact (user, session_key) pair: a stale/old session
    # logging out can never remove a newer session's pointer, because its
    # own session_key will no longer equal the current pointer's value.
    ActiveSession.objects.filter(user=user, session_key=session_key).delete()
