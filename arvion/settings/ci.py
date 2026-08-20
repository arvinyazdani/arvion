"""Settings used by the GitHub Actions quality workflow."""

import os

import dj_database_url

from .local import *  # noqa: F403


DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

database_url = os.environ.get("DATABASE_URL", "")
if not database_url.lower().startswith(("postgresql://", "postgres://")):
    raise RuntimeError("CI requires a PostgreSQL DATABASE_URL")

DATABASES = {
    "default": dj_database_url.parse(
        database_url,
        conn_max_age=0,
        conn_health_checks=False,
    )
}

# CI must never contact real email, SMS, storage, or payment services.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
SMS_BACKEND = "core.sms.backends.ConsoleSMSBackend"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
