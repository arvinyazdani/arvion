"""Best-effort IndexNow notifications for public URL changes."""
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger(__name__)

# IndexNow keys are intentionally public and must be served at this exact
# root-level URL so they authorize notifications for every site path.
INDEXNOW_KEY = "71aa4375d1314eb1ba38df693b58f60a"


def submit_urls(urls):
    if not getattr(settings, "INDEXNOW_ENABLED", False):
        return {"status": "disabled", "count": 0}
    origin = settings.SITE_URL.rstrip("/")
    parsed_origin = urlsplit(origin)
    accepted = []
    for url in dict.fromkeys(urls):
        parsed = urlsplit(url)
        if parsed.scheme == parsed_origin.scheme and parsed.netloc == parsed_origin.netloc and parsed.path:
            accepted.append(url)
    if not accepted:
        return {"status": "empty", "count": 0}
    payload = json.dumps({
        "host": parsed_origin.netloc,
        "key": INDEXNOW_KEY,
        "keyLocation": f"{origin}/{INDEXNOW_KEY}.txt",
        "urlList": accepted[:10000],
    }).encode("utf-8")
    request = Request("https://api.indexnow.org/indexnow", data=payload,
                       headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
    try:
        with urlopen(request, timeout=1.5) as response:
            status = response.status
    except HTTPError as error:
        status = error.code
    except (URLError, TimeoutError, OSError) as error:
        logger.warning("IndexNow notification failed (%s)", error.__class__.__name__)
        return {"status": "failed", "count": len(accepted)}
    if status not in (200, 202):
        logger.warning("IndexNow notification returned HTTP %s", status)
        return {"status": "rejected", "http_status": status, "count": len(accepted)}
    logger.info("IndexNow accepted notification batch: http=%s urls=%s", status, len(accepted))
    return {"status": "accepted" if status == 200 else "pending_validation", "http_status": status, "count": len(accepted)}
