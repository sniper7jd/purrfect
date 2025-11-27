"""Global context processors."""
from django.conf import settings


def global_settings(request):
    """Add global settings to template context."""
    context = {
        'PLACES_API_KEY': settings.PLACES_API_KEY,
        'DEBUG': settings.DEBUG,
    }
    
    # Add unread message count for authenticated users
    if request.user.is_authenticated:
        try:
            from chat.models import Message
            unread_count = Message.objects.filter(
                conversation__participants=request.user,
                read_at__isnull=True
            ).exclude(sender=request.user).count()
            context['unread_message_count'] = unread_count
        except Exception:
            # Handle case where chat app might not be loaded
            context['unread_message_count'] = 0
    else:
        context['unread_message_count'] = 0
    
    return context



