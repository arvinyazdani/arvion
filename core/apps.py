from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = "تنظیمات سایت"

    def ready(self):
        from . import admin_config  # noqa: F401
        from . import indexnow_signals  # noqa: F401
