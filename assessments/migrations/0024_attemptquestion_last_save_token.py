from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("assessments", "0023_set_exam_prices_to_two_million")]

    operations = [
        migrations.AddField(
            model_name="attemptquestion",
            name="last_save_token",
            field=models.CharField(blank=True, editable=False, max_length=36),
        ),
    ]
