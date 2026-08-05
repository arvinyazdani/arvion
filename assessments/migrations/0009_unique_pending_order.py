from django.db import migrations, models


def keep_one_pending_order(apps, schema_editor):
    Order = apps.get_model("assessments", "Order")
    pairs = Order.objects.filter(status="pending").values_list("user_id", "exam_id").distinct()
    for user_id, exam_id in pairs:
        pending = Order.objects.filter(
            user_id=user_id, exam_id=exam_id, status="pending",
        ).order_by("-created_at")
        keep = pending.first()
        if keep:
            pending.exclude(pk=keep.pk).update(status="cancelled")


class Migration(migrations.Migration):
    dependencies = [("assessments", "0008_attempt_completion_reason")]

    operations = [
        migrations.RunPython(keep_one_pending_order, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="order",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "pending")),
                fields=("user", "exam"),
                name="unique_pending_order_per_user_exam",
            ),
        ),
    ]
