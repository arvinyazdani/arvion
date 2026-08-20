from django.db import migrations, models
from django.db.models import F


def backfill_snapshot_choice_ids(apps, schema_editor):
    AttemptQuestion = apps.get_model("assessments", "AttemptQuestion")
    AttemptQuestion.objects.filter(
        selected_choice__isnull=False,
        selected_choice_snapshot_id__isnull=True,
    ).update(selected_choice_snapshot_id=F("selected_choice_id"))


class Migration(migrations.Migration):
    dependencies = [("assessments", "0017_backfill_order_customer_records")]

    operations = [
        migrations.AddField(
            model_name="attemptquestion",
            name="selected_choice_snapshot_id",
            field=models.PositiveBigIntegerField(blank=True, editable=False, null=True),
        ),
        migrations.RunPython(backfill_snapshot_choice_ids, migrations.RunPython.noop),
    ]
