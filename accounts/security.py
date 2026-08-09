import hashlib

from django.core.cache import cache


def client_address(request):
    """Return the address supplied by the trusted application server.

    X-Forwarded-For is deliberately ignored here: unless every proxy hop is
    controlled it is attacker supplied and makes a poor throttling identity.
    """
    return request.META.get("REMOTE_ADDR") or "unknown"


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
