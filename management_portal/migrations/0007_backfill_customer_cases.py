from django.db import migrations


def backfill(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    CustomerCase = apps.get_model("management_portal", "CustomerCase")
    CaseDocument = apps.get_model("management_portal", "CaseDocument")
    CaseActivity = apps.get_model("management_portal", "CaseActivity")
    sources = [
        ("leads", "Lead", "lead", lambda x: x.business_name or x.name, lambda x: x.name, lambda x: x.phone or "", lambda x: x.email_or_telegram if "@" in x.email_or_telegram else "", lambda x: x.message, "درخواست همکاری اولیه"),
        ("crm_orders", "CrmOrder", "crm", lambda x: x.organization_name, lambda x: x.contact_name, lambda x: x.phone, lambda x: x.work_email, lambda x: x.main_pain_points, "فرم نیازسنجی اولیه CRM"),
        ("clinic_orders", "ClinicOrder", "clinic", lambda x: x.clinic_name, lambda x: x.contact_name, lambda x: x.phone, lambda x: x.work_email, lambda x: x.main_pain_points, "فرم نیازسنجی اولیه کلینیک"),
    ]
    stage_map = {"contacted": "discovery"}
    for app_label, model_name, kind, name, contact, phone, email, summary, title in sources:
        Model = apps.get_model(app_label, model_name)
        content_type, _ = ContentType.objects.get_or_create(app_label=app_label, model=model_name.lower())
        for item in Model.objects.all().iterator():
            stage = stage_map.get(item.status, item.status)
            if stage not in {"new", "discovery", "qualified", "proposal", "won", "lost"}: stage = "new"
            case, created = CustomerCase.objects.get_or_create(source_content_type=content_type, source_object_id=item.pk, defaults={"kind": kind, "customer_name": name(item), "contact_name": contact(item), "phone": phone(item), "email": email(item), "stage": stage, "summary": summary(item)})
            CaseDocument.objects.get_or_create(case=case, content_type=content_type, object_id=item.pk, kind="initial", defaults={"title": title})
            if created: CaseActivity.objects.create(case=case, kind="system", title="پرونده مشتری از اطلاعات موجود ساخته شد", body=title)


class Migration(migrations.Migration):
    dependencies = [
        ("management_portal", "0006_customercase_casetask_casedocument_caseactivity_and_more"),
        ("leads", "0004_lead_sales_workflow"),
        ("crm_orders", "0003_crmspecialistdiscovery"),
        ("clinic_orders", "0001_initial"),
    ]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
