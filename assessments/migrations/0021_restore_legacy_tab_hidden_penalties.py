from django.db import migrations
from django.db.models import Count


def restore_legacy_penalties(apps, schema_editor):
    Attempt = apps.get_model("assessments", "Attempt")
    IntegrityEvent = apps.get_model("assessments", "IntegrityEvent")
    legacy_counts = (
        IntegrityEvent.objects.filter(event_type="tab_hidden")
        .values("attempt_id")
        .annotate(total=Count("id"))
    )
    for row in legacy_counts.iterator():
        attempt = Attempt.objects.filter(pk=row["attempt_id"]).only("integrity_score").first()
        if attempt is None:
            continue
        restored_points = min(row["total"], 5) * 2
        Attempt.objects.filter(pk=attempt.pk).update(
            integrity_score=min(100, attempt.integrity_score + restored_points)
        )
    IntegrityEvent.objects.filter(event_type__in=("tab_hidden", "window_blur")).update(
        metadata={"legacy_unreliable": True}
    )


class Migration(migrations.Migration):
    dependencies = [("assessments", "0020_alter_integrityevent_event_type")]

    operations = [
        migrations.RunPython(restore_legacy_penalties, migrations.RunPython.noop),
    ]
