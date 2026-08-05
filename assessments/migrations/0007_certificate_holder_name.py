from django.db import migrations, models


def snapshot_holder_names(apps, schema_editor):
    Certificate = apps.get_model("assessments", "Certificate")
    for certificate in Certificate.objects.select_related("result__attempt__user"):
        user = certificate.result.attempt.user
        name = f"{user.first_name} {user.last_name}".strip() or "Arvion Candidate"
        certificate.holder_name = name
        certificate.save(update_fields=["holder_name"])


class Migration(migrations.Migration):
    dependencies = [("assessments", "0006_attemptquestion_audio_play_count_question_audio_path_and_more")]

    operations = [
        migrations.AddField(
            model_name="certificate",
            name="holder_name",
            field=models.CharField(default="", max_length=300),
        ),
        migrations.RunPython(snapshot_holder_names, migrations.RunPython.noop),
    ]
