from django.db import migrations, models


def copy_existing_totals(apps, schema_editor):
    Order = apps.get_model("assessments", "Order")
    for order in Order.objects.all().only("pk", "amount_irr").iterator():
        order.subtotal_irr = order.amount_irr
        order.save(update_fields=["subtotal_irr"])


class Migration(migrations.Migration):
    dependencies = [("assessments", "0013_supportticket")]

    operations = [
        migrations.AddField(model_name="order", name="subtotal_irr", field=models.PositiveIntegerField(default=0)),
        migrations.AddField(model_name="order", name="discount_irr", field=models.PositiveIntegerField(default=0)),
        migrations.AddField(model_name="order", name="discount_percent", field=models.PositiveSmallIntegerField(default=0)),
        migrations.RunPython(copy_existing_totals, migrations.RunPython.noop),
    ]
