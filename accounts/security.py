import hashlib
import ipaddress

from django.conf import settings
from django.core.cache import cache


def client_address(request):
    """Return the address supplied by the trusted application server.

    Only a validated X-Real-IP from an explicitly trusted reverse proxy is
    accepted. X-Forwarded-For remains ignored because its hop chain is easy to
    misconfigure and attacker-controlled at the public edge.
    """
    peer = request.META.get("REMOTE_ADDR") or ""
    candidate = request.META.get("HTTP_X_REAL_IP", "") if peer in settings.TRUSTED_PROXY_IPS else peer
    try:
        return ipaddress.ip_address(candidate.strip()).compressed
    except ValueError:
        return "unknown"


def normalized_fingerprint(value):
    normalized = (value or "").strip().casefold().encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()[:24]


class AttemptThrottle:
    def __init__(self, namespace, request, identity, limit, window_seconds):
        address = normalized_fingerprint(client_address(request))
        subject = normalized_fingerprint(identity)
        self.key = f"security:{namespace}:{address}:{subject}"
        self.limit = limit
        self.window_seconds = window_seconds

    def blocked(self):
        return int(cache.get(self.key, 0)) >= self.limit

    def failure(self):
        try:
            count = cache.incr(self.key)
        except ValueError:
            cache.set(self.key, 1, self.window_seconds)
            count = 1
        return count

    def success(self):
        cache.delete(self.key)
