import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-local-arvion-key")
DEBUG = False
ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "accounts",
    "assessments",
    "core",
    "blog",
    "projects",
    "services",
    "leads",
    "crm_orders",
    "traffic",
    "taggit",
    "widget_tweaks",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "traffic.middleware.TrafficAnalyticsMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "arvion.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "core" / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "core.context_processors.assessment_flags",
        "core.context_processors.seo_context",
    ]},
}]
WSGI_APPLICATION = "arvion.wsgi.application"
ASGI_APPLICATION = "arvion.asgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fa"
LANGUAGES = [("fa", "فارسی"), ("en", "English")]
SITE_URL = os.getenv("SITE_URL", "https://rvin-tech.com").rstrip("/")
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "home"
EMAIL_VERIFICATION_TIMEOUT = 60 * 60 * 24
EMAIL_VERIFICATION_RESEND_SECONDS = int(os.getenv("EMAIL_VERIFICATION_RESEND_SECONDS", "120"))
AUTH_LOGIN_ATTEMPTS = int(os.getenv("AUTH_LOGIN_ATTEMPTS", "5"))
AUTH_LOGIN_WINDOW_SECONDS = int(os.getenv("AUTH_LOGIN_WINDOW_SECONDS", "900"))
AUTH_EMAIL_REQUESTS = int(os.getenv("AUTH_EMAIL_REQUESTS", "4"))
AUTH_EMAIL_WINDOW_SECONDS = int(os.getenv("AUTH_EMAIL_WINDOW_SECONDS", "3600"))

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Rvion <noreply@rvin-tech.com>")
CONTACT_NOTIFICATION_EMAIL = os.getenv("CONTACT_NOTIFICATION_EMAIL", "owner@rvin-tech.com")
LEAD_RATE_LIMIT_SECONDS = int(os.getenv("LEAD_RATE_LIMIT_SECONDS", "60"))
PAYMENT_GATEWAY = os.getenv("PAYMENT_GATEWAY", "sandbox")
CARD_PAYMENT_NUMBER = os.getenv("CARD_PAYMENT_NUMBER", "6219861821208849")
CARD_PAYMENT_HOLDER = os.getenv("CARD_PAYMENT_HOLDER", "آروین یزدانی")
ASSESSMENT_FREE_CHECKOUT = os.getenv("ASSESSMENT_FREE_CHECKOUT", "0") == "1"
ASSESSMENT_ATTEMPTS_PER_DAY = int(os.getenv("ASSESSMENT_ATTEMPTS_PER_DAY", "5"))
ASSESSMENT_INTEGRITY_REVIEW_THRESHOLD = int(os.getenv("ASSESSMENT_INTEGRITY_REVIEW_THRESHOLD", "80"))
ASSESSMENT_TERMS_VERSION = os.getenv("ASSESSMENT_TERMS_VERSION", "2026-08-05")
ASSESSMENT_SUPPORT_TICKETS_PER_HOUR = int(os.getenv("ASSESSMENT_SUPPORT_TICKETS_PER_HOUR", "5"))
