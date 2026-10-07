"""Short-lived, actor-bound SMS review and durable at-most-once submission."""
import hashlib
import json
from uuid import uuid4, UUID

from django.core import signing

from .models import SMSCampaign

SALT = "management-sms-preview-v1"


def signature(audience, recipients, message):
    payload = json.dumps([audience, sorted(recipients), message], ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def make_preview(actor, audience, recipients, message):
    # No phone or message content travels in the signed hidden field.
    return signing.dumps({"actor": actor.pk, "nonce": str(uuid4()),
                          "digest": signature(audience, recipients, message)}, salt=SALT)


def check_preview(token, actor, audience, recipients, message):
    data = signing.loads(token, salt=SALT, max_age=900)
    if data.get("actor") != actor.pk or data.get("digest") != signature(audience, recipients, message):
        raise signing.BadSignature("preview changed")
    return UUID(data["nonce"])


def claim_campaign(token, actor, audience, recipients, message):
    # Unique DB key arbitrates concurrent/replayed POSTs. This claim must commit
    # before provider calls; the view is explicitly outside ATOMIC_REQUESTS.
    return SMSCampaign.objects.get_or_create(submission_token=token, defaults={
        "audience": audience, "message": message, "recipient_count": len(recipients),
        "created_by": actor,
    })
