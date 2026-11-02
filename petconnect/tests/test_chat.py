import base64
import json

import jwt
import pytest
from django.urls import reverse

from chat import realtime
from chat.models import Conversation, Message

pytestmark = pytest.mark.django_db

ABLY_SECRET = "a-test-secret-that-is-at-least-32-bytes"
ABLY_KEY = f"appid.keyid:{ABLY_SECRET}"


@pytest.fixture
def friend(make_user):
    return make_user("bob")


@pytest.fixture
def conversation(user, friend):
    conv = Conversation.objects.create()
    conv.participants.add(user, friend)
    return conv


@pytest.fixture
def published(monkeypatch):
    calls = []
    monkeypatch.setattr(realtime, "publish", lambda *args: calls.append(args) or True)
    return calls


@pytest.mark.parametrize(
    ("name", "method"),
    [
        ("chat:conversation", "get"),
        ("chat:get_messages", "get"),
        ("chat:send_message", "post"),
        ("chat:mark_read", "post"),
        ("chat:token", "get"),
    ],
)
def test_non_participants_get_404(client, make_user, conversation, name, method):
    client.force_login(make_user("eve"))
    response = getattr(client, method)(reverse(name, args=[conversation.id]))
    assert response.status_code == 404


def test_send_message_saves_and_publishes(
    auth_client, conversation, user, published, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        response = auth_client.post(
            reverse("chat:send_message", args=[conversation.id]), {"content": "Park at 10?"}
        )

    assert response.status_code == 201
    message = Message.objects.get()
    assert message.sender == user and message.content == "Park at 10?"
    channel, name, payload = published[0]
    assert channel == f"chat:{conversation.id}"
    assert name == "message"
    assert payload["id"] == message.id


@pytest.mark.parametrize("content", ["", "   ", "x" * 2001])
def test_send_message_validates_content(auth_client, conversation, content):
    response = auth_client.post(
        reverse("chat:send_message", args=[conversation.id]), {"content": content}
    )
    assert response.status_code == 400
    assert not Message.objects.exists()


def test_get_messages_after_id(auth_client, conversation, user, friend):
    first = Message.objects.create(conversation=conversation, sender=friend, content="one")
    second = Message.objects.create(conversation=conversation, sender=user, content="two")
    data = auth_client.get(
        reverse("chat:get_messages", args=[conversation.id]), {"after": first.id}
    ).json()
    assert [m["id"] for m in data["messages"]] == [second.id]


def test_opening_conversation_marks_messages_read(auth_client, conversation, friend):
    message = Message.objects.create(conversation=conversation, sender=friend, content="hi")
    auth_client.get(reverse("chat:conversation", args=[conversation.id]))
    message.refresh_from_db()
    assert message.read_at is not None


def test_conversation_escapes_message_content(auth_client, conversation, friend):
    Message.objects.create(
        conversation=conversation, sender=friend, content="<script>alert(1)</script>"
    )
    body = auth_client.get(reverse("chat:conversation", args=[conversation.id])).content.decode()
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in body


def test_chat_messages_do_not_leak_into_flash_messages(auth_client, conversation, friend):
    Message.objects.create(conversation=conversation, sender=friend, content="only once please")
    body = auth_client.get(reverse("chat:conversation", args=[conversation.id])).content.decode()
    assert body.count("only once please") == 1
    assert 'id="flash-messages"' not in body


def test_token_unavailable_without_ably(auth_client, conversation):
    response = auth_client.get(reverse("chat:token", args=[conversation.id]))
    assert response.status_code == 503


def test_token_is_scoped_to_one_conversation(auth_client, conversation, user, settings):
    settings.ABLY_API_KEY = ABLY_KEY
    response = auth_client.get(reverse("chat:token", args=[conversation.id]))

    assert response.status_code == 200
    assert response["Content-Type"] == "application/jwt"
    token = response.content.decode()
    assert jwt.get_unverified_header(token)["kid"] == "appid.keyid"
    claims = jwt.decode(token, ABLY_SECRET, algorithms=["HS256"])
    assert claims["x-ably-clientId"] == str(user.pk)
    assert json.loads(claims["x-ably-capability"]) == {
        f"chat:{conversation.id}": ["subscribe"],
        f"typing:{conversation.id}": ["publish", "subscribe"],
    }
    assert claims["exp"] - claims["iat"] == realtime.TOKEN_TTL_SECONDS


def test_publish_calls_ably_rest(monkeypatch, settings):
    settings.ABLY_API_KEY = ABLY_KEY
    captured = {}

    class FakeResponse:
        status = 201

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(realtime.urllib.request, "urlopen", fake_urlopen)

    assert realtime.publish("chat:7", "message", {"id": 1}) is True
    request = captured["request"]
    assert request.full_url == "https://rest.ably.io/channels/chat%3A7/messages"
    assert (
        request.headers["Authorization"] == "Basic " + base64.b64encode(ABLY_KEY.encode()).decode()
    )
    body = json.loads(request.data)
    assert body == {"name": "message", "data": '{"id": 1}', "encoding": "json"}


def test_publish_is_a_noop_without_key(settings):
    settings.ABLY_API_KEY = ""
    assert realtime.publish("chat:1", "message", {}) is False


def test_publish_swallows_network_errors(monkeypatch, settings):
    settings.ABLY_API_KEY = ABLY_KEY

    def boom(*args, **kwargs):
        raise realtime.urllib.error.URLError("offline")

    monkeypatch.setattr(realtime.urllib.request, "urlopen", boom)
    assert realtime.publish("chat:1", "message", {}) is False


def test_inbox_shows_last_message_and_unread(auth_client, conversation, user, friend, make_user):
    Message.objects.create(conversation=conversation, sender=friend, content="first")
    Message.objects.create(conversation=conversation, sender=friend, content="latest")
    for name in ("carol", "dave"):
        other = make_user(name)
        conv = Conversation.objects.create()
        conv.participants.add(user, other)
        Message.objects.create(conversation=conv, sender=other, content=f"hi from {name}")

    response = auth_client.get(reverse("chat:inbox"))

    conversations = {c.id: c for c in response.context["conversations"]}
    assert conversations[conversation.id].last_message_content == "latest"
    assert conversations[conversation.id].unread_count == 2
    assert conversations[conversation.id].other_participants == [friend]


def test_start_conversation_reuses_existing(auth_client, conversation, friend):
    response = auth_client.get(reverse("chat:start", args=[friend.id]))
    assert response.url == reverse("chat:conversation", args=[conversation.id])
    assert Conversation.objects.count() == 1
