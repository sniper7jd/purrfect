"""Global context processors."""
from django.conf import settings


def global_settings(request):
    """Add global settings to template context."""
    return {
        'PLACES_API_KEY': settings.PLACES_API_KEY,
        'DEBUG': settings.DEBUG,
    }



