"""ASGI entry point (the app is served with gunicorn/WSGI in production)."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "petconnect.settings")

application = get_asgi_application()
