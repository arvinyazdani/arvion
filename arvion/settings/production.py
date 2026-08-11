import os

import dj_database_url

from .base import *  # noqa: F403

ASSESSMENT_FREE_CHECKOUT = False

required = [
    "DJANGO_SECRET_KEY", "DATABASE_URL", "DJANGO_ALLOWED_HOSTS",
    "DEFAULT_FROM_EMAIL", "CONTACT_NOTIFICATION_EMAIL",
    "PAYMENT_GATEWAY",
]
USE_S3_STORAGE = os.getenv("USE_S3_STORAGE", "1") == "1"
USE_SMTP_EMAIL = os.getenv("USE_SMTP_EMAIL", "1") == "1"
if USE_SMTP_EMAIL:
    required += ["EMAIL_HOST_USER", "EMAIL_HOST_PASSWORD"]
if USE_S3_STORAGE:
    required += ["AWS_STORAGE_BUCKET_NAME", "AWS_S3_ENDPOINT_URL", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
if SMS_BACKEND == "core.sms.backends.MelipayamakSMSBackend":
    required += [
        "MELIPAYAMAK_USERNAME", "MELIPAYAMAK_PASSWORD",
        "MELIPAYAMAK_SENDER_NUMBER",
    ]
missing = [name for name in required if not os.getenv(name)]
if missing:
    raise RuntimeError(f"Missing production environment variables: {', '.join(missing)}")

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
if len(SECRET_KEY) < 50 or SECRET_KEY.startswith("replace-"):
    raise RuntimeError("DJANGO_SECRET_KEY must be a unique random value of at least 50 characters")
if not os.environ["DATABASE_URL"].lower().startswith(("postgresql://", "postgres://")):
    raise RuntimeError("DATABASE_URL must use PostgreSQL in production")
DATABASES = {"default": dj_database_url.config(conn_max_age=600, conn_health_checks=True, ssl_require=True)}
EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
    if USE_SMTP_EMAIL else "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.postmarkapp.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = True
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "10"))

if USE_S3_STORAGE:
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
    AWS_STORAGE_BUCKET_NAME = os.environ["AWS_STORAGE_BUCKET_NAME"]
    AWS_S3_ENDPOINT_URL = os.environ["AWS_S3_ENDPOINT_URL"].rstrip("/")
    AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
    AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "auto")
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_CUSTOM_DOMAIN = os.getenv("AWS_S3_CUSTOM_DOMAIN", "")
    MEDIA_URL = (
        f"https://{AWS_S3_CUSTOM_DOMAIN}/" if AWS_S3_CUSTOM_DOMAIN
        else f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/"
    )

CSRF_TRUSTED_ORIGINS = [url.strip() for url in os.getenv("CSRF_TRUSTED_ORIGINS", "https://rvionai.com,https://www.rvionai.com").split(",")]
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "1") == "1"
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "1") == "1"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "1") == "1"
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000" if SECURE_SSL_REDIRECT else "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_HSTS_PRELOAD = SECURE_HSTS_SECONDS > 0
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"

if PAYMENT_GATEWAY in {"sandbox", "free"}:
    raise RuntimeError("PAYMENT_GATEWAY must be card_transfer or a real production provider")
