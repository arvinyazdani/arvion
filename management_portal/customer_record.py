"""Read-only presentation of the existing customer ledger and domain records."""
from uuid import UUID
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.urls import reverse

from assessments.models import Attempt, AttemptResult, ManualPaymentSubmission, Order, SupportTicket
from contracts.models import ContractAcceptance, ContractProposal, ContractReview
from .models import CaseActivity, CaseTask, CustomerEvent


CATEGORIES = {
    "identity": ("عضویت", "Account"), "sales": ("نیازسنجی", "Discovery"),
    "order": ("سفارش", "Order"), "payment": ("پرداخت", "Payment"),
    "assessment": ("آزمون", "Assessment"), "contract": ("قرارداد", "Contract"),
    "support": ("پشتیبانی", "Support"), "communication": ("ارتباط", "Contact"),
    "task": ("پیگیری", "Follow-up"), "system": ("سیستم", "System"),
}


def _representatives(query, filters):
    """Keep journey state correct even when a relevant record is on a later page."""
    records = {}
    for condition in [Q(), *filters]:
        item = query.filter(condition).first()
        if item:
            records[item.pk] = item
    return list(records.values())


def _event_links(events, customer, user_ids, user):
    """Resolve only scoped existing sources in batches; never trust ledger metadata URLs."""
    groups = {}
    for event in events:
        groups.setdefault(event.source_type, set()).add(event.source_id)
    links = {}
    labels = {}

    def ids(kind):
        return {int(value) for value in groups.get(kind, ()) if value.isascii() and value.isdigit() and len(value) <= 18}

    def uuid_ids(kind):
        valid = set()
        for value in groups.get(kind, ()):
            try:
                valid.add(UUID(value))
            except (ValueError, TypeError, AttributeError):
                pass
        return valid

    activities = list(CaseActivity.objects.filter(pk__in=ids("management_portal.caseactivity"), case__customer=customer))
    content_types = {ct.pk: f"{ct.app_label}.{ct.model}" for ct in ContentType.objects.filter(pk__in=[a.metadata.get("content_type") for a in activities if isinstance(a.metadata.get("content_type"), int)])}
    activity_sources = {}
    for activity in activities:
        ct_id = activity.metadata.get("content_type")
        kind = content_types.get(ct_id) if isinstance(ct_id, int) else None
        source_id = str(activity.metadata.get("object_id", ""))
        if kind and kind != "management_portal.caseactivity" and source_id:
            groups.setdefault(kind, set()).add(source_id)
            activity_sources[activity.pk] = (kind, source_id)

    for item in ManualPaymentSubmission.objects.filter(pk__in=ids("assessments.manualpaymentsubmission"), order__customer=customer):
        if user.has_perm("assessments.view_manualpaymentsubmission"):
            links[("assessments.manualpaymentsubmission", str(item.pk))] = reverse("management_portal:approvals") + f"?payment={item.pk}#payment-{item.pk}"
    for kind, model in (("assessments.attempt", Attempt), ("assessments.attemptresult", AttemptResult)):
        scope = {"user_id__in": user_ids} if model is Attempt else {"attempt__user_id__in": user_ids}
        rows = model.objects.filter(pk__in=uuid_ids(kind) if model is Attempt else ids(kind), **scope)
        fields = ("pk", "user_id", "exam__title_fa", "exam__title_en") if model is Attempt else ("pk", "attempt__user_id", "attempt_id")
        for row in rows.values_list(*fields):
            links[(kind, str(row[0]))] = reverse("management_portal:customer_assessment_detail", args=[customer.pk, row[1]]) + f"#attempt-{row[0] if model is Attempt else row[2]}"
            if model is Attempt:
                labels[(kind, str(row[0]))] = (row[2], row[3])
    for order in Order.objects.filter(pk__in=uuid_ids("assessments.order"), user_id__in=user_ids).select_related("exam"):
        links[("assessments.order", str(order.pk))] = reverse("management_portal:customer_assessment_detail", args=[customer.pk, order.user_id]) + f"#order-{order.pk}"
        labels[("assessments.order", str(order.pk))] = (order.exam.title_fa, order.exam.title_en)
    if user.has_perm("assessments.view_supportticket") or user.has_perm("assessments.view_exam"):
        for ticket in SupportTicket.objects.filter(pk__in=ids("assessments.supportticket"), user_id__in=user_ids):
            links[("assessments.supportticket", str(ticket.pk))] = reverse("management_portal:assessment_support") + f"?ticket={ticket.pk}#ticket-{ticket.pk}"
    if user.is_superuser:
        for contract in ContractProposal.objects.filter(pk__in=ids("contracts.contractproposal"), customer=customer):
            links[("contracts.contractproposal", str(contract.pk))] = reverse("management_portal:contract_detail", args=[contract.pk])
        for kind, model in (("contracts.contractacceptance", ContractAcceptance), ("contracts.contractreview", ContractReview)):
            for pk, proposal_id in model.objects.filter(pk__in=ids(kind), version__proposal__customer=customer).values_list("pk", "version__proposal_id"):
                links[(kind, str(pk))] = reverse("management_portal:contract_detail", args=[proposal_id])
    for activity in activities:
        key = ("management_portal.caseactivity", str(activity.pk))
        underlying = activity_sources.get(activity.pk)
        links[key] = links.get(underlying, reverse("management_portal:workspace_detail", args=[activity.case_id]))
    return links, labels


def customer_record(request, customer):
    lang = getattr(request, "LANGUAGE_CODE", "fa")
    index = int(lang == "en")
    contacts = list(customer.contacts.all())
    user_ids = {contact.user_id for contact in contacts if contact.user_id}
    orders = Order.objects.filter(Q(customer=customer) | Q(customer__isnull=True, user_id__in=user_ids)).select_related("exam", "user", "manual_payment").order_by("-created_at", "-pk")
    user_ids.update(orders.values_list("user_id", flat=True))
    attempts = Attempt.objects.filter(user_id__in=user_ids).select_related("user", "exam", "result").order_by("-created_at", "-pk")
    contracts = customer.contracts.order_by("-updated_at", "-pk")
    cases = customer.cases.select_related("owner", "source_content_type").annotate(document_count=Count("documents", distinct=True)).order_by("-updated_at", "-pk")
    ledger = CustomerEvent.objects.filter(customer=customer).select_related("actor", "case")
    category = request.GET.get("event_kind", "")
    last_activity = ledger.first()
    if category in CATEGORIES:
        ledger = ledger.filter(category=category)
    else:
        category = ""
    event_page = Paginator(ledger, 15).get_page(request.GET.get("events_page"))
    events = list(event_page.object_list)
    links, labels = _event_links(events, customer, user_ids, request.user)
    timeline = []
    for event in events:
        key = (event.source_type, event.source_id)
        detail = labels[key][index] if key in labels else event.description
        source_labels = {
            "management_portal.caseactivity": ("رویداد پرونده", "Case activity"),
            "assessments.manualpaymentsubmission": ("رسید پرداخت", "Payment receipt"),
            "assessments.order": ("سفارش آزمون", "Assessment order"),
            "assessments.attempt": ("تلاش آزمون", "Assessment attempt"),
            "assessments.attemptresult": ("نتیجه آزمون", "Assessment result"),
        }
        timeline.append({"at": event.occurred_at, "kind": event.category,
                         "title": event.title_en if index else event.title_fa,
                         "detail": detail, "url": links.get(key, ""),
                         "source": source_labels.get(event.source_type, CATEGORIES.get(event.category, CATEGORIES["system"]))[index],
                         "meta": event.case.code if event.case_id else "",
                         "actor": event.actor.get_full_name() or event.actor.email if event.actor_id else ("ثبت‌کننده مشخص نیست" if not index else "No actor recorded")})
    pages = {name: Paginator(query, 15).get_page(request.GET.get(name + "_page"))
             for name, query in (("attempts", attempts), ("orders", orders), ("contracts", contracts), ("cases", cases))}
    for case in pages["cases"]:
        case.record_stage = {"new": ("جدید", "New"), "discovery": ("نیازسنجی", "Discovery"), "qualified": ("واجد شرایط", "Qualified"), "proposal": ("پیشنهاد", "Proposal"), "won": ("موفق", "Won"), "lost": ("بسته‌شده", "Closed")}.get(case.stage, ("نامشخص", "Unknown"))[index]
    tasks = CaseTask.objects.filter(case__customer=customer, status="open").select_related("assigned_to", "case")
    unique_accounts = {}
    for contact in contacts:
        if contact.user_id:
            unique_accounts.setdefault(contact.user_id, contact)
    return {"events": timeline, "event_page": event_page, "event_kind": category,
            "account_contacts": list(unique_accounts.values()),
            "event_categories": [(key, value[index]) for key, value in CATEGORIES.items()],
            "last_activity": last_activity, "record_pages": pages,
            "attempts": pages["attempts"], "orders": pages["orders"], "contracts": pages["contracts"], "cases": pages["cases"],
            "open_tasks": list(tasks[:10]), "open_task_count": tasks.count(),
            "journey_orders": _representatives(orders, [Q(status="pending"), Q(status="pending", manual_payment__status="pending"), Q(status="paid")]),
            "journey_attempts": _representatives(attempts, [Q(status="completed"), Q(status__in=("ready", "in_progress", "submitted", "scoring"))]),
            "journey_contracts": _representatives(contracts, [Q(status="accepted"), Q(status__in=("sent", "review"))])}
