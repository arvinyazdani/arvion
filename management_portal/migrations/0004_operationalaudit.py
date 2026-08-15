from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("management_portal", "0003_smsdispatch")]
    operations = [
        migrations.CreateModel(
            name="OperationalAudit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(db_index=True, max_length=60)),
                ("target_type", models.CharField(db_index=True, max_length=60)),
                ("target_id", models.CharField(db_index=True, max_length=80)),
                ("summary", models.CharField(max_length=240)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="management_operations", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "رویداد عملیاتی", "verbose_name_plural": "سابقه عملیات", "ordering": ("-created_at",)},
        )
    ]
