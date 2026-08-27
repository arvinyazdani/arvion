from django.db import migrations


def backfill_events(apps, schema_editor):
    CustomerContact = apps.get_model("management_portal", "CustomerContact")
    CustomerEvent = apps.get_model("management_portal", "CustomerEvent")
    CaseActivity = apps.get_model("management_portal", "CaseActivity")
    Order = apps.get_model("assessments", "Order")
    Attempt = apps.get_model("assessments", "Attempt")
    AttemptResult = apps.get_model("assessments", "AttemptResult")
    ContractProposal = apps.get_model("contracts", "ContractProposal")
    rows = []

    def add(**values):
        rows.append(CustomerEvent(**values))
        if len(rows) >= 500:
            CustomerEvent.objects.bulk_create(rows, ignore_conflicts=True, batch_size=500)
            rows.clear()

    for contact in CustomerContact.objects.exclude(user_id=None).select_related("user").iterator():
        add(customer_id=contact.customer_id, category="identity", event_type="account_created", title_fa="عضویت در سایت", title_en="Website account created", description=contact.user.email or contact.user.mobile or contact.name, source_type="accounts.user", source_id=str(contact.user_id), dedupe_key=f"accounts.user:{contact.user_id}:account_created", occurred_at=contact.user.date_joined)
    for order in Order.objects.exclude(customer_id=None).select_related("exam").iterator():
        add(customer_id=order.customer_id, category="order", event_type="order_created", title_fa="سفارش آزمون ثبت شد", title_en="Assessment order created", description=order.exam.title_fa, source_type="assessments.order", source_id=str(order.pk), dedupe_key=f"order:{order.pk}:created", occurred_at=order.created_at)
        if order.paid_at:
            add(customer_id=order.customer_id, category="payment", event_type="order_paid", title_fa="پرداخت سفارش تأیید شد", title_en="Order payment approved", description=str(order.amount_irr), source_type="assessments.order", source_id=str(order.pk), dedupe_key=f"order:{order.pk}:paid", occurred_at=order.paid_at)
    for attempt in Attempt.objects.select_related("entitlement__order", "exam").iterator():
        customer_id = attempt.entitlement.order.customer_id
        if customer_id:
            started = bool(attempt.started_at)
            add(
                customer_id=customer_id,
                category="assessment",
                event_type="assessment_started" if started else "assessment_access_created",
                title_fa="آزمون شروع شد" if started else "دسترسی آزمون ایجاد شد",
                title_en="Assessment started" if started else "Assessment access created",
                description=attempt.exam.title_fa,
                source_type="assessments.attempt",
                source_id=str(attempt.pk),
                dedupe_key=f"attempt:{attempt.pk}:{'started' if started else 'access'}",
                occurred_at=attempt.started_at or attempt.created_at,
            )
    for result in AttemptResult.objects.select_related("attempt__entitlement__order").iterator():
        customer_id = result.attempt.entitlement.order.customer_id
        if customer_id:
            add(customer_id=customer_id, category="assessment", event_type="assessment_completed", title_fa="نتیجه آزمون آماده شد", title_en="Assessment result ready", description=f"{result.level_code} · {result.percentage}%", source_type="assessments.attemptresult", source_id=str(result.pk), dedupe_key=f"assessments.attemptresult:{result.pk}:assessment_completed", occurred_at=result.generated_at)
    for proposal in ContractProposal.objects.exclude(customer_id=None).iterator():
        add(customer_id=proposal.customer_id, case_id=proposal.customer_case_id, category="contract", event_type="contract_created", title_fa="پیش‌نویس قرارداد ساخته شد", title_en="Contract draft created", description=proposal.project_title, source_type="contracts.contractproposal", source_id=str(proposal.pk), dedupe_key=f"contracts.contractproposal:{proposal.pk}:contract_created", actor_id=proposal.created_by_id, occurred_at=proposal.created_at)
    for activity in CaseActivity.objects.exclude(case__customer_id=None).select_related("case").iterator():
        add(customer_id=activity.case.customer_id, case_id=activity.case_id, category="task" if activity.kind == "task" else "communication" if activity.kind in {"call", "message", "meeting"} else "sales", event_type=f"case_{activity.kind}", title_fa=activity.title, title_en=activity.title, description=activity.body, source_type="management_portal.caseactivity", source_id=str(activity.pk), dedupe_key=f"management_portal.caseactivity:{activity.pk}:case_{activity.kind}", actor_id=activity.actor_id, occurred_at=activity.created_at)
    if rows:
        CustomerEvent.objects.bulk_create(rows, ignore_conflicts=True, batch_size=500)


class Migration(migrations.Migration):
    dependencies = [("management_portal", "0015_savedcustomersegment_customerevent_and_more")]
    operations = [migrations.RunPython(backfill_events, migrations.RunPython.noop)]
