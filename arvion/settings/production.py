import os

import dj_database_url

from .base import *  # noqa: F403

required = ["DJANGO_SECRET_KEY", "DATABASE_URL", "DJANGO_ALLOWED_HOSTS"]
missing = [name for name in required if not os.getenv(name)]
if missing:
    raise RuntimeError(f"Missing production environment variables: {', '.join(missing)}")

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DATABASES = {"default": dj_database_url.config(conn_max_age=600, conn_health_checks=True, ssl_require=True)}
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.postmarkapp.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = True

CSRF_TRUSTED_ORIGINS = [url.strip() for url in os.getenv("CSRF_TRUSTED_ORIGINS", "https://rvin-tech.com,https://www.rvin-tech.com").split(",")]
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

if PAYMENT_GATEWAY == "sandbox":
    raise RuntimeError("PAYMENT_GATEWAY must be configured for production")
