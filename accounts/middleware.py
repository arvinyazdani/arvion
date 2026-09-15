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

    ActiveSession is the authorization boundary for a *new* login
    superseding an old one. This middleware checks that pointer before the
    view and flushes a stale session without deleting an in-flight login's
    Session row. It is also the security boundary for the legacy-rollout
    case: an already-authenticated session
    that predates this feature (no ActiveSession row yet) and for two such
    legacy sessions racing to be recognised as the account's one session —
    neither of those has a fresh login event to hook into, so they must be
    caught here, on every authenticated request.

    Performance: the overwhelmingly common case — a session that already
    owns the account's pointer — is a single, lock-free, read-only SELECT
    (`_enforce_current_session` below). Parallel requests from the same
    legitimate session (exam autosave, dashboard polling, etc.) must never
    contend with each other for a write lock; only a *mismatch* pays for a
    `transaction.atomic()` + `select_for_update()` on the User row, and
    only long enough to make and re-check that one decision.

    Known, accepted limitation: a request from the soon-to-be-superseded
    session that was *already in flight* — past this middleware's check —
    at the exact instant a new login elsewhere changes the pointer cannot
    be retroactively cancelled; it completes as if it had won. Only that
    session's *next* request is guaranteed to see the mismatch and be
    logged out. This is inherent to request-scoped, not connection- or
    query-scoped, enforcement.

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

        # Fast path: one read-only SELECT, no transaction, no row lock.
        # This must be cheap and non-blocking, since it runs on every
        # authenticated customer request.
        current_pointer = ActiveSession.objects.filter(user_id=user.pk).values_list("session_key", flat=True).first()
        if current_pointer == session_key:
            return

        # Slow path: reached only when there is no ActiveSession yet (a
        # legacy session claiming it for the first time) or the fast-path
        # read saw a different key (a genuine loser, or simply a stale read
        # racing someone else's own claim). Lock the User row — not
        # ActiveSession directly — so every writer (this middleware and
        # accounts.signals' login receiver) serializes through the same
        # gate; that alone is enough to make the read-modify-write on this
        # user's single ActiveSession row safe.
        with transaction.atomic():
            locked_user = User.objects.select_for_update().get(pk=user.pk)
            active, _ = ActiveSession.objects.get_or_create(
                user=locked_user, defaults={"session_key": session_key},
            )
            # Re-check under the lock: the world may have moved on between
            # the fast-path read above and acquiring this lock — another
            # request could have already claimed the pointer for this very
            # session in the meantime, and must not be logged out for it.
            if active.session_key == session_key:
                return
        # Still a mismatch after the authoritative re-check: this session
        # no longer owns the account's pointer. Sign it out now,
        # unconditionally, before any messaging is attempted.
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

            # cache.delete() returning True/False for "was this key
            # actually present" is a documented part of Django's cache API
            # and is atomic for every backend this project configures
            # (LocMemCache: a single call under its own internal lock;
            # FileBasedCache: os.remove()'s FileNotFoundError is caught and
            # turned into False rather than a double removal; RedisCache:
            # Redis's DEL is a single atomic server-side command). So of
            # any number of requests racing to consume the same marker, at
            # most one delete() call can return True — that request alone
            # shows the message.
            marker_key = session_invalidation_marker_key(session_key)
            consumed = cache.delete(marker_key)
        except Exception:
            return
        if not consumed:
            return
        try:
            lang = getattr(request, "LANGUAGE_CODE", "fa")
            messages.info(request, _invalidated_message(lang))
        except Exception:
            pass
