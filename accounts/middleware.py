from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.db import transaction

from .models import ActiveSession, User
from .signals import is_single_session_enforced, session_invalidation_marker_key


def _invalidated_message(lang):
    return (
        "این دستگاه از حساب شما خارج شد چون در جای دیگری وارد شدید."
        if lang == "fa" else
        "You were signed out here because you signed in elsewhere."
    )


class SingleSessionMiddleware:
    """Enforces (and explains) the one-active-session-per-account rule.

    This middleware is NOT the security boundary for a *new* login
    superseding an old one — that is enforced immediately, at login time,
    by deleting the old Session row (accounts.signals). It IS the security
    boundary for the legacy-rollout case: an already-authenticated session
    that predates this feature (no ActiveSession row yet) and for two such
    legacy sessions racing to be recognised as the account's one session —
    neither of those has a fresh login event to hook into, so they must be
    caught here, on every authenticated request, fail-closed.

    Failure of the cache-backed courtesy message must never block this
    enforcement: the `try/except` below only ever wraps the message-only
    path, never the session check or the `logout()` call.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            self._enforce_current_session(request, user)
        elif user is not None:
            self._maybe_show_invalidated_message(request)
        return self.get_response(request)

    def _enforce_current_session(self, request, user):
        if not is_single_session_enforced(user):
            return
        session_key = request.session.session_key
        if not session_key:
            return
        with transaction.atomic():
            locked_user = User.objects.select_for_update().get(pk=user.pk)
            active, _ = ActiveSession.objects.select_for_update().get_or_create(
                user=locked_user, defaults={"session_key": session_key},
            )
            if active.session_key == session_key:
                return
        # This request's session no longer owns the account's pointer —
        # either it lost a legacy-claim race, or a newer login elsewhere
        # has since replaced it. The outcome is identical either way: sign
        # it out now, unconditionally, before any messaging is attempted.
        logout(request)
        try:
            lang = getattr(request, "LANGUAGE_CODE", "fa")
            messages.info(request, _invalidated_message(lang))
        except Exception:
            pass

    def _maybe_show_invalidated_message(self, request):
        # Not request.session.session_key: once AuthenticationMiddleware's
        # lazy request.user is evaluated (above) for a session whose row no
        # longer exists, Django's own session-loading clears session_key to
        # None. The cookie the browser actually sent is unaffected by that
        # and is the only reliable way to know which session this was.
        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
        if not session_key:
            return
        try:
            from django.core.cache import cache

            marker_key = session_invalidation_marker_key(session_key)
            found = cache.get(marker_key)
            if found:
                cache.delete(marker_key)
        except Exception:
            return
        if not found:
            return
        try:
            lang = getattr(request, "LANGUAGE_CODE", "fa")
            messages.info(request, _invalidated_message(lang))
        except Exception:
            pass
