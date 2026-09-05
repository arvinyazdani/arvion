from django.db import migrations


PRICE_IRR = 2_000_000
PREVIOUS = {"english-placement-a1-c1": 1_200_000, "python-django-professional": 500_000}


def set_prices(apps, schema_editor):
    Exam = apps.get_model("assessments", "Exam")
    Exam.objects.filter(slug__in=PREVIOUS).update(price_irr=PRICE_IRR)


def restore_prices(apps, schema_editor):
    Exam = apps.get_model("assessments", "Exam")
    for slug, price in PREVIOUS.items():
        Exam.objects.filter(slug=slug).update(price_irr=price)


class Migration(migrations.Migration):

    dependencies = [("assessments", "0022_alter_exam_price_irr")]

    operations = [migrations.RunPython(set_prices, restore_prices)]
