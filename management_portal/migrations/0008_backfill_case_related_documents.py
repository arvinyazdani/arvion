from django.db import migrations
from django.db.models import Q


def backfill_related(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    CustomerCase = apps.get_model("management_portal", "CustomerCase")
    CaseDocument = apps.get_model("management_portal", "CaseDocument")
    CaseActivity = apps.get_model("management_portal", "CaseActivity")
    Discovery = apps.get_model("crm_orders", "CrmSpecialistDiscovery")
    Proposal = apps.get_model("contracts", "ContractProposal")
    crm_type, _ = ContentType.objects.get_or_create(app_label="crm_orders", model="crmorder")
    discovery_type, _ = ContentType.objects.get_or_create(app_label="crm_orders", model="crmspecialistdiscovery")
    contract_type, _ = ContentType.objects.get_or_create(app_label="contracts", model="contractproposal")
    for discovery in Discovery.objects.all().iterator():
        case = CustomerCase.objects.filter(source_content_type=crm_type, source_object_id=discovery.order_id).first()
        if not case: continue
        _, created = CaseDocument.objects.get_or_create(case=case, content_type=discovery_type, object_id=discovery.pk, kind="specialist", defaults={"title": "فرم نیازسنجی تخصصی CRM", "snapshot": discovery.answers})
        if created: CaseActivity.objects.create(case=case, kind="document", title="سند موجود به پرونده متصل شد", body="فرم نیازسنجی تخصصی CRM")
    for proposal in Proposal.objects.all().iterator():
        query = Q(phone=proposal.customer_phone)
        if proposal.customer_email: query |= Q(email__iexact=proposal.customer_email)
        case = CustomerCase.objects.filter(query).first()
        if not case: continue
        title = ("قرارداد تأییدشده: " if proposal.status == "accepted" else "قرارداد: ") + proposal.project_title
        _, created = CaseDocument.objects.get_or_create(case=case, content_type=contract_type, object_id=proposal.pk, kind="contract", defaults={"title": title, "created_by_id": proposal.created_by_id})
        if proposal.status == "accepted": CustomerCase.objects.filter(pk=case.pk).update(stage="won")
        if created: CaseActivity.objects.create(case=case, kind="document", title="قرارداد موجود به پرونده متصل شد", body=title, actor_id=proposal.created_by_id)


class Migration(migrations.Migration):
    dependencies = [("management_portal", "0007_backfill_customer_cases"), ("contracts", "0001_initial"), ("crm_orders", "0003_crmspecialistdiscovery")]
    operations = [migrations.RunPython(backfill_related, migrations.RunPython.noop)]
