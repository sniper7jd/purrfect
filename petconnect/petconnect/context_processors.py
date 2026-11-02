"""Global template context."""

from django.conf import settings


def global_settings(request):
    context = {
        "DEMO_LOGIN_ENABLED": settings.DEMO_LOGIN_ENABLED,
        "SOURCE_CODE_URL": settings.SOURCE_CODE_URL,
        "unread_message_count": 0,
    }
    if request.user.is_authenticated:
        from chat.models import Message

        context["unread_message_count"] = (
            Message.objects.filter(conversation__participants=request.user, read_at__isnull=True)
            .exclude(sender=request.user)
            .count()
        )
    return context
