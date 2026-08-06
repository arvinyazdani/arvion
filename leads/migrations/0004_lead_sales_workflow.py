import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone

import leads.models.lead


class Migration(migrations.Migration):
    dependencies = [("leads", "0003_alter_lead_request_type"), ("services", "0004_service_sales_content")]
    operations = [
        migrations.AddField(model_name="lead", name="tracking_code", field=models.CharField(default=leads.models.lead.lead_tracking_code, editable=False, max_length=12, unique=True)),
        migrations.AddField(model_name="lead", name="business_name", field=models.CharField(blank=True, max_length=160)),
        migrations.AddField(model_name="lead", name="website_url", field=models.URLField(blank=True)),
        migrations.AddField(model_name="lead", name="service", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="leads", to="services.service")),
        migrations.AddField(model_name="lead", name="budget_range", field=models.CharField(choices=[("unsure", "Not sure yet"), ("under_50", "Under 50 million toman"), ("50_150", "50–150 million toman"), ("150_500", "150–500 million toman"), ("over_500", "Over 500 million toman")], default="unsure", max_length=20)),
        migrations.AddField(model_name="lead", name="timeline", field=models.CharField(choices=[("flexible", "Flexible"), ("one_month", "Within one month"), ("one_three", "One to three months"), ("over_three", "More than three months")], default="flexible", max_length=20)),
        migrations.AddField(model_name="lead", name="preferred_contact", field=models.CharField(choices=[("phone", "Phone"), ("email", "Email"), ("telegram", "Telegram")], default="phone", max_length=12)),
        migrations.AddField(model_name="lead", name="privacy_accepted_at", field=models.DateTimeField(default=timezone.now), preserve_default=False),
        migrations.AddField(model_name="lead", name="status", field=models.CharField(choices=[("new", "New"), ("contacted", "Contacted"), ("qualified", "Qualified"), ("proposal", "Proposal sent"), ("won", "Won"), ("lost", "Lost")], db_index=True, default="new", max_length=12)),
        migrations.AlterField(model_name="lead", name="request_type", field=models.CharField(choices=[("consultation", "Consultation"), ("website", "Website"), ("webapp", "Web application"), ("ecommerce", "E-commerce"), ("support", "Support and optimization"), ("training", "Training Request"), ("other", "Other")], default="consultation", max_length=20, verbose_name="Request Type")),
        migrations.AlterModelOptions(name="lead", options={"ordering": ("-created_at",)}),
    ]
