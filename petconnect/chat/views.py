"""Chat views."""

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, IntegerField, OuterRef, Prefetch, Subquery
from django.db.models.functions import Coalesce
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from . import realtime
from .models import Conversation, Message

User = get_user_model()

MAX_MESSAGE_LENGTH = 2000


def serialize_message(message):
    return {
        "id": message.id,
        "content": message.content,
        "sender_id": message.sender_id,
        "sent_at": message.sent_at.isoformat(),
    }


def _conversation_for(user, conversation_id):
    return get_object_or_404(Conversation, pk=conversation_id, participants=user)


@login_required
def inbox(request):
    latest = Message.objects.filter(conversation=OuterRef("pk")).order_by("-sent_at")
    unread = Message.objects.filter(conversation=OuterRef("pk"), read_at__isnull=True).exclude(
        sender=request.user
    )
    conversations = (
        Conversation.objects.filter(participants=request.user)
        .annotate(
            last_message_content=Subquery(latest.values("content")[:1]),
            last_message_sent_at=Subquery(latest.values("sent_at")[:1]),
            last_message_sender_id=Subquery(latest.values("sender_id")[:1]),
            unread_count=Coalesce(
                Subquery(
                    unread.order_by().values("conversation").annotate(n=Count("pk")).values("n"),
                    output_field=IntegerField(),
                ),
                0,
            ),
        )
        .prefetch_related(
            Prefetch(
                "participants",
                queryset=User.objects.exclude(pk=request.user.pk),
                to_attr="other_participants",
            )
        )
        .order_by("-last_message_sent_at", "-updated_at")
    )
    return render(request, "chat/inbox.html", {"conversations": conversations})


@login_required
def conversation(request, conversation_id):
    conv = _conversation_for(request.user, conversation_id)
    other_user = conv.participants.exclude(pk=request.user.pk).first()
    messages = list(conv.messages.select_related("sender"))
    marked = (
        conv.messages.filter(read_at__isnull=True)
        .exclude(sender=request.user)
        .update(read_at=timezone.now())
    )
    if marked:
        transaction.on_commit(
            lambda: realtime.publish(
                realtime.message_channel(conv.id), "read", {"reader_id": request.user.id}
            )
        )

    chat_config = {
        "conversationId": conv.id,
        "currentUserId": request.user.id,
        "otherUserName": (other_user.name or other_user.username) if other_user else "",
        "realtime": realtime.is_enabled(),
        "tokenUrl": reverse("chat:token", args=[conv.id]),
        "sendUrl": reverse("chat:send_message", args=[conv.id]),
        "messagesUrl": reverse("chat:get_messages", args=[conv.id]),
        "readUrl": reverse("chat:mark_read", args=[conv.id]),
        "messageChannel": realtime.message_channel(conv.id),
        "typingChannel": realtime.typing_channel(conv.id),
        "lastMessageId": messages[-1].id if messages else 0,
    }
    return render(
        request,
        "chat/conversation.html",
        {
            "conversation": conv,
            "other_user": other_user,
            "chat_messages": messages,
            "show_seen": bool(
                messages and messages[-1].sender_id == request.user.id and messages[-1].read_at
            ),
            "chat_config": chat_config,
        },
    )


@login_required
def start_conversation(request, user_id):
    other_user = get_object_or_404(User, pk=user_id)
    if other_user == request.user:
        return redirect("chat:inbox")

    # Annotate before filtering so the count covers all participants, not just the joined row.
    existing = (
        Conversation.objects.annotate(size=Count("participants"))
        .filter(size=2, participants=request.user)
        .filter(participants=other_user)
        .first()
    )
    if existing:
        return redirect("chat:conversation", conversation_id=existing.id)

    conv = Conversation.objects.create()
    conv.participants.add(request.user, other_user)
    return redirect("chat:conversation", conversation_id=conv.id)


@login_required
@require_GET
def get_messages(request, conversation_id):
    """Messages newer than `?after=<id>`: used for catch-up and the polling fallback."""
    conv = _conversation_for(request.user, conversation_id)
    messages = conv.messages.all()
    after = request.GET.get("after", "")
    if after.isdigit():
        messages = messages.filter(id__gt=int(after))
    return JsonResponse({"messages": [serialize_message(m) for m in messages[:200]]})


@login_required
@require_POST
def send_message(request, conversation_id):
    conv = _conversation_for(request.user, conversation_id)
    content = request.POST.get("content", "").strip()
    if not content:
        return JsonResponse({"error": "Message can't be empty."}, status=400)
    if len(content) > MAX_MESSAGE_LENGTH:
        return JsonResponse({"error": "Message is too long."}, status=400)

    message = Message.objects.create(conversation=conv, sender=request.user, content=content)
    Conversation.objects.filter(pk=conv.pk).update(updated_at=timezone.now())

    payload = serialize_message(message)
    transaction.on_commit(
        lambda: realtime.publish(realtime.message_channel(conv.id), "message", payload)
    )
    return JsonResponse({"message": payload}, status=201)


@login_required
@require_POST
def mark_read(request, conversation_id):
    conv = _conversation_for(request.user, conversation_id)
    marked = (
        conv.messages.filter(read_at__isnull=True)
        .exclude(sender=request.user)
        .update(read_at=timezone.now())
    )
    if marked:
        transaction.on_commit(
            lambda: realtime.publish(
                realtime.message_channel(conv.id), "read", {"reader_id": request.user.id}
            )
        )
    return JsonResponse({"marked": marked})


@login_required
@require_GET
def token(request, conversation_id):
    """Ably auth endpoint (the browser SDK's `authUrl`)."""
    conv = _conversation_for(request.user, conversation_id)
    if not realtime.is_enabled():
        return JsonResponse({"error": "Realtime is not configured."}, status=503)
    response = HttpResponse(
        realtime.create_token(request.user, conv.id), content_type="application/jwt"
    )
    response["Cache-Control"] = "no-store"
    return response
