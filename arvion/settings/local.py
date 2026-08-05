from .base import *  # noqa: F403

DEBUG = True
ASSESSMENT_FREE_CHECKOUT = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
