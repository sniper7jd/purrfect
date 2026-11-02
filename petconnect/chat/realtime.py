"""Ably integration.

The server publishes chat messages over Ably's REST API, and browsers receive them over
Ably's realtime connection using short-lived JWTs minted here. Each token is scoped to one
conversation: subscribe-only on the message channel (so clients can't forge messages) and
publish+subscribe on the typing channel.
"""

import base64
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request

import jwt
from django.conf import settings

logger = logging.getLogger(__name__)

TOKEN_TTL_SECONDS = 60 * 60
PUBLISH_TIMEOUT_SECONDS = 3


def is_enabled():
    return bool(settings.ABLY_API_KEY)


def message_channel(conversation_id):
    return f"chat:{conversation_id}"


def typing_channel(conversation_id):
    return f"typing:{conversation_id}"


def create_token(user, conversation_id):
    key_name, key_secret = settings.ABLY_API_KEY.split(":", 1)
    now = int(time.time())
    capability = {
        message_channel(conversation_id): ["subscribe"],
        typing_channel(conversation_id): ["publish", "subscribe"],
    }
    claims = {
        "iat": now,
        "exp": now + TOKEN_TTL_SECONDS,
        "x-ably-capability": json.dumps(capability),
        "x-ably-clientId": str(user.pk),
    }
    return jwt.encode(claims, key_secret, algorithm="HS256", headers={"kid": key_name})


def publish(channel, name, data):
    """Publish one message; failures are logged, never raised (the DB is the source of truth)."""
    if not is_enabled():
        return False

    url = (
        f"https://{settings.ABLY_REST_HOST}/channels/"
        f"{urllib.parse.quote(channel, safe='')}/messages"
    )
    body = json.dumps({"name": name, "data": json.dumps(data), "encoding": "json"}).encode()
    credentials = base64.b64encode(settings.ABLY_API_KEY.encode()).decode()
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Basic {credentials}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=PUBLISH_TIMEOUT_SECONDS) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError) as exc:
        logger.warning("Ably publish to %s failed: %s", channel, exc)
        return False
