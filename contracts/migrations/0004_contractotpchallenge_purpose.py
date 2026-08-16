from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("contracts", "0003_contractproposal_customer")]

    operations = [
        migrations.AddField(
            model_name="contractotpchallenge",
            name="purpose",
            field=models.CharField(choices=[("access", "ورود به اتاق قرارداد"), ("acceptance", "تأیید نهایی قرارداد")], default="acceptance", max_length=12),
        ),
    ]
