from django.apps import AppConfig


class ManagementPortalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "management_portal"
    verbose_name = "مدیریت آرویون"

    def ready(self):
        from . import signals  # noqa: F401
