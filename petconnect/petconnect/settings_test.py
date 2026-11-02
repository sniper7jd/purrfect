"""Settings for the pytest suite."""

import os
import tempfile

os.environ.setdefault("SECRET_KEY", "test-only-secret-key")
os.environ.setdefault("DEBUG", "False")

from .settings import *  # noqa: E402

MEDIA_ROOT = tempfile.mkdtemp(prefix="petconnect-test-media-")
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
ABLY_API_KEY = ""
SENTRY_DSN = ""
