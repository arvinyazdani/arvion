"""Management surfaces for the unified customer project workspace.

This module intentionally sits outside the legacy contract views.  It gives
staff one case-centred workflow while the old public URLs and records remain
available during the migration window.
"""

from __future__ import annotations

from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.db.models import OuterRef, Prefetch, Q, Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from contracts.forms import (
    GeneralTermsRevisionForm,
    QuestionnaireRowFormSet,
    WorkspaceAccessForm,
    WorkspaceContractForm,
    questionnaire_rows_from_schema,
    questionnaire_schema_from_formset,
)
from contracts.models import ContractProposal, ContractVersion, RoomAccessGrant, SpecialistAssignment
from contracts.services import proposal_snapshot
from contracts.workspace_services import (
    create_access_grant,
    create_general_terms_version,
    create_specialist_template_version,
    current_general_terms,
    ensure_case_workspace,
    generate_access_password,
    publish_customer_workspace,
    revoke_access_grant,
    send_workspace_access,
    workspace_access_url,
    workspace_progress,
)

from .cases import DEMO_SELECTION_DOCUMENT_TITLE
from .models import CustomerCase, OperationalAudit
from .order_journey import STATUS_EN, preparation, source_links
from .assessment_review import review_page


DASH = "—"


def _lang(request):
    return "en" if getattr(request, "LANGUAGE_CODE", "fa") == "en" else "fa"


def _message(request, fa, en):
    return fa if _lang(request) == "fa" else en


def _validation_text(error):
    if hasattr(error, "messages"):
        return " ".join(error.messages)
    return str(error)


def _workspace_for_case(case):
    return (
        case.contract_proposals.select_related(
            "customer", "general_terms_version", "created_by", "specialist_assignment__version"
        )
        .prefetch_related(
            "access_grants",
            Prefetch("versions", queryset=ContractVersion.objects.select_related("acceptance").prefetch_related("room_acknowledgements")), "clauses",
        )
        .exclude(status__in=("expired",))
        .order_by("-updated_at", "-pk")
        .first()
    )


def _flatten_snapshot(value, prefix=""):
    """Turn archived JSON into readable label/value rows without losing data."""
    rows = []
    if isinstance(value, dict):
        for key, child in value.items():
            label = f"{prefix} / {key}" if prefix else str(key)
            rows.extend(_flatten_snapshot(child, label))
    elif isinstance(value, list):
        rendered = "، ".join(str(item) for item in value) if value else "—"
        rows.append((prefix, rendered))
    else:
        rows.append((prefix, "—" if value in (None, "") else str(value)))
    return rows


DOCUMENT_KIND_EN = {
    "initial": "Initial discovery", "specialist": "Specialist discovery",
    "contract": "Agreement", "payment": "Payment", "export": "Export",
    "attachment": "Attachment",
}

def _demo_selection_card(document, case, lang):
    """Bilingual, structured facts for the case page's "Demo selection"
    section, read from a frozen CaseDocument snapshot (see
    `cases.sync_demo_selection_document`) — never from a live
    DemoSelection, so this never touches `public_token`/`session_key` and
    keeps working even after the underlying selection is cleaned up."""
    if not document:
        return None
    data = document.snapshot or {}
    features = data.get(f"features_{lang}") or []
    slug = data.get("demo_template_slug")
    return {
        "template_title": data.get(f"template_title_{lang}", DASH),
        "category_label": data.get(f"category_{lang}", DASH),
        "brand": data.get("brand") or DASH,
        "theme_label": data.get(f"theme_{lang}", DASH),
        "personality_label": data.get(f"personality_{lang}", DASH),
        "features_display": ("، " if lang == "fa" else ", ").join(features) if features else DASH,
        "brief_rows": data.get(f"brief_{lang}") or [],
        "public_url": reverse("projects:demo_preview", args=[slug]) if slug else "",
        "request_url": reverse("management_portal:request_detail", args=["lead", case.source_object_id]) if case.kind == "lead" and case.source_object_id else "",
    }


EVENT_LABEL_EN = {
    "workspace_created": "Workspace created", "access_created": "Access created",
    "access_rotated": "Access rotated", "access_revoked": "Access revoked",
    "link_sent": "Link sent", "link_copied": "Link copied",
    "delivery_failed": "Delivery failed", "login_succeeded": "Successful sign-in",
    "login_failed": "Failed sign-in", "session_expired": "Session expired",
    "form_saved": "Form saved", "form_conflict": "Save conflict",
    "form_submitted": "Form submitted", "general_viewed": "General terms viewed",
    "general_accepted": "General terms accepted", "private_viewed": "Private terms viewed",
    "private_accepted": "Private terms accepted", "final_accepted": "Final acceptance",
    "logout": "Signed out",
}


@staff_member_required(login_url="accounts:login")
def workspace_list(request):
    lang = _lang(request)
    query = request.GET.get("q", "").strip()[:150]
    state = request.GET.get("state", "all")
    state = state if state in {"all", "not_started", "draft", "sent", "accepted", "revoked"} else "all"
    proposal_queryset = (
        ContractProposal.objects.exclude(status="expired")
        .select_related("specialist_assignment__version")
        .prefetch_related(Prefetch("versions", queryset=ContractVersion.objects.select_related("acceptance").prefetch_related("room_acknowledgements")))
        .order_by("-updated_at", "-pk")
    )
    latest = ContractProposal.objects.filter(customer_case_id=OuterRef("pk")).exclude(status="expired").order_by("-updated_at", "-pk")
    all_cases = CustomerCase.objects.annotate(workspace_status=Subquery(latest.values("status")[:1]))
    cases = (
        all_cases.select_related("customer", "owner")
        .prefetch_related(Prefetch("contract_proposals", queryset=proposal_queryset, to_attr="workspace_proposals"))
        .order_by("-updated_at", "-pk")
    )
    if query:
        cases = cases.filter(
            Q(code__icontains=query)
            | Q(customer_name__icontains=query)
            | Q(contact_name__icontains=query)
            | Q(phone__icontains=query)
            | Q(email__icontains=query)
        )
    if state == "not_started":
        cases = cases.filter(workspace_status__isnull=True)
    elif state == "draft":
        cases = cases.filter(workspace_status="draft")
    elif state == "sent":
        cases = cases.filter(workspace_status__in=("sent", "review"))
    elif state == "accepted":
        cases = cases.filter(workspace_status="accepted")
    elif state == "revoked":
        cases = cases.filter(workspace_status="revoked")

    rows = []
    page = review_page(cases, request, "page", "workspace-cases")
    for case in page:
        proposal = case.workspace_proposals[0] if case.workspace_proposals else None
        if proposal:
            try:
                assignment = proposal.specialist_assignment
            except SpecialistAssignment.DoesNotExist:
                assignment = None
            version = next(
                (item for item in proposal.versions.all() if item.number == proposal.current_version),
                None,
            ) if proposal.current_version else None
            progress = workspace_progress(proposal, assignment=assignment, version=version)
        else:
            progress = None
        rows.append({"case": case, "proposal": proposal, "progress": progress,
                     "status_label": proposal.get_status_display() if lang == "fa" and proposal else STATUS_EN.get(proposal.status, proposal.status) if proposal else ""})

    return render(request, "management_portal/v2/workspace_list.html", {
        "lang": lang,
        "rows": rows,
        "page": page,
        "query": query,
        "state": state,
        "stats": {
            "all": all_cases.count(),
            "not_started": all_cases.filter(workspace_status__isnull=True).count(),
            "active": all_cases.filter(workspace_status="draft").count(),
            "accepted": all_cases.filter(workspace_status="accepted").count(),
        },
    })


@staff_member_required(login_url="accounts:login")
def workspace_detail(request, case_id):
    lang = _lang(request)
    case = get_object_or_404(
        CustomerCase.objects.select_related("customer", "owner", "source_content_type")
        .prefetch_related("documents__revisions", "activities__actor", "tasks"),
        pk=case_id,
    )
    proposal = _workspace_for_case(case)
    return render(request, "management_portal/v2/workspace_detail.html", _workspace_context(request, case, proposal))


def _workspace_context(request, case, proposal, contract_form=None):
    lang = _lang(request)
    assignment = None
    progress = None
    if proposal:
        assignment = getattr(proposal, "specialist_assignment", None)
        version = next((v for v in proposal.versions.all() if v.number == proposal.current_version), None)
        progress = workspace_progress(proposal, assignment=assignment, version=version)
    credentials = request.session.pop(f"workspace_credentials_{case.pk}", None) if request.method == "GET" else None
    case_documents = list(case.documents.all())
    demo_document = next((document for document in case_documents if document.title == DEMO_SELECTION_DOCUMENT_TITLE), None)
    documents = [
        {
            "document": document,
            "rows": _flatten_snapshot(document.snapshot),
            "revisions": document.revisions.all(),
            "revision_rows": [{"revision": r, "rows": _flatten_snapshot(r.snapshot)} for r in document.revisions.all()],
            "kind_label": document.get_kind_display() if lang == "fa" else DOCUMENT_KIND_EN.get(document.kind, document.kind),
        }
        for document in case_documents
        if document is not demo_document
    ]
    demo_card = _demo_selection_card(demo_document, case, lang)
    events_page = review_page(proposal.room_events.select_related("actor").order_by("-created_at", "-pk"), request, "events_page", "activity") if proposal else None
    room_events = [
        {
            "event": event,
            "label": event.get_event_type_display() if lang == "fa" else EVENT_LABEL_EN.get(event.event_type, event.event_type.replace("_", " ").title()),
        }
        for event in (events_page if events_page is not None else [])
    ]
    checks = preparation(case, proposal, assignment, lang)
    return {
        "lang": lang,
        "case": case,
        "proposal": proposal,
        "assignment": assignment,
        "progress": progress,
        "documents": documents,
        "demo_card": demo_card,
        "room_events": room_events,
        "events_page": events_page,
        "credentials": credentials,
        "contract_form": contract_form if contract_form is not None else WorkspaceContractForm(instance=proposal, lang=lang) if proposal else None,
        "preparation": checks,
        "ready_to_publish": bool(proposal and all(c["ready"] for c in checks)),
        "source_links": source_links(case, request.user),
        "proposal_status_label": proposal.get_status_display() if proposal and lang == "fa" else STATUS_EN.get(proposal.status, proposal.status) if proposal else "",
        "amount_display": f"{proposal.amount_irr:,}" if proposal else "",
        "access_form": WorkspaceAccessForm(
            lang=lang,
            initial={"authorized_phone": case.phone or (case.customer.phone if case.customer else "")},
        ) if proposal else None,
        "access_url": workspace_access_url(proposal, absolute_base=request.build_absolute_uri("/")) if proposal else "",
    }


@staff_member_required(login_url="accounts:login")
def workspace_preview(request, case_id):
    """Staff-only, read-only review; no publication, credentials or room events."""
    case = get_object_or_404(CustomerCase, pk=case_id)
    proposal = _workspace_for_case(case)
    if proposal is None:
        messages.info(request, _message(request, "ابتدا فضای مشتری را بسازید.", "Create the workspace first."))
        return redirect("management_portal:workspace_detail", case_id=case.pk)
    version = next((v for v in proposal.versions.all() if v.number == proposal.current_version), None)
    snapshot = version.snapshot if version else proposal_snapshot(proposal)
    general = snapshot.get("general_terms", "")
    if version is None and proposal.general_terms_version_id:
        general = proposal.general_terms_version.body
    return render(request, "management_portal/v2/workspace_preview.html", {
        "lang": _lang(request), "case": case, "published": version is not None,
        "project_title": snapshot.get("project_title", ""), "customer_name": snapshot.get("customer_name", ""),
        "scope": snapshot.get("project_scope", ""), "payment_terms": snapshot.get("payment_terms", ""),
        "delivery_terms": snapshot.get("delivery_terms", ""), "client_details": snapshot.get("client_details", ""),
        "general": general, "private": snapshot.get("private_terms", ""),
        "clauses": snapshot.get("clauses", []),
        "sections": snapshot.get("specialist_questionnaire", {}).get("schema", []),
        "amount_display": f'{snapshot.get("amount_irr", 0):,}',
    })


@staff_member_required(login_url="accounts:login")
@require_POST
def workspace_create(request, case_id):
    case = get_object_or_404(CustomerCase, pk=case_id)
    proposal, created = ensure_case_workspace(case=case, actor=request.user)
    if created:
        messages.success(request, _message(
            request,
            "فضای اختصاصی مشتری ساخته شد. حالا فرم تخصصی و شرایط خصوصی را آماده کنید.",
            "The customer workspace is ready. Add the specialist form and private terms next.",
        ))
        OperationalAudit.objects.create(
            actor=request.user, action="workspace_created", target_type="customer_case",
            target_id=str(case.pk), summary=case.customer_name,
        )
    else:
        messages.info(request, _message(request, "فضای فعال همین پرونده باز شد.", "The active workspace was opened."))
    return redirect("management_portal:workspace_detail", case_id=case.pk)


@staff_member_required(login_url="accounts:login")
@require_POST
def workspace_contract_save(request, case_id):
    case = get_object_or_404(CustomerCase, pk=case_id)
    proposal = get_object_or_404(ContractProposal, customer_case=case, pk=request.POST.get("proposal_id"))
    if proposal.status not in {"draft", "revoked"} or proposal.current_version:
        messages.error(request, _message(request, "نسخه منتشرشده قابل ویرایش نیست.", "A published version cannot be edited."))
        return redirect("management_portal:workspace_detail", case_id=case.pk)
    form = WorkspaceContractForm(request.POST, instance=proposal, lang=_lang(request))
    if form.is_valid():
        form.save()
        OperationalAudit.objects.create(
            actor=request.user, action="workspace_contract_updated", target_type="contract_proposal",
            target_id=str(proposal.pk), summary=proposal.project_title,
        )
        messages.success(request, _message(request, "اطلاعات تجاری و شرایط خصوصی ذخیره شد.", "Commercial and private terms were saved."))
    else:
        messages.error(request, _message(request, "فیلدهای مشخص‌شده را اصلاح کنید.", "Correct the highlighted fields."))
        return render(request, "management_portal/v2/workspace_detail.html",
                      _workspace_context(request, case, proposal, contract_form=form), status=400)
    return redirect("management_portal:workspace_detail", case_id=case.pk)


@staff_member_required(login_url="accounts:login")
def workspace_questionnaire(request, case_id):
    lang = _lang(request)
    case = get_object_or_404(CustomerCase, pk=case_id)
    proposal = _workspace_for_case(case)
    if proposal is None:
        messages.warning(request, _message(request, "ابتدا فضای مشتری را بسازید.", "Create the customer workspace first."))
        return redirect("management_portal:workspace_detail", case_id=case.pk)
    assignment = getattr(proposal, "specialist_assignment", None)
    initial = questionnaire_rows_from_schema(assignment.version.schema) if assignment else [{
        "section_title": "شناخت نیاز اصلی" if lang == "fa" else "Core requirements",
        "section_description": "" if lang == "fa" else "",
        "question_label": "" if lang == "fa" else "",
        "help_text": "", "placeholder": "", "answer_type": "long_text", "required": True,
    }]
    formset = QuestionnaireRowFormSet(request.POST or None, initial=initial, prefix="questions", form_kwargs={"lang": lang})
    if request.method == "POST" and formset.is_valid():
        try:
            schema = questionnaire_schema_from_formset(formset)
            assignment = create_specialist_template_version(
                proposal=proposal, schema=schema, actor=request.user,
                name=request.POST.get("template_name", "").strip() or None,
                change_note=request.POST.get("change_note", "").strip(),
            )
        except (ValidationError, ValueError) as exc:
            messages.error(request, _validation_text(exc))
        else:
            OperationalAudit.objects.create(
                actor=request.user, action="workspace_questionnaire_version_created",
                target_type="contract_proposal", target_id=str(proposal.pk),
                summary=assignment.version.template.name,
                metadata={"version": assignment.version.number},
            )
            messages.success(request, _message(request, "نسخه فرم تخصصی ذخیره شد.", "The specialist form version was saved."))
            return redirect("management_portal:workspace_detail", case_id=case.pk)
    elif request.method == "POST":
        messages.error(request, _message(request, "سؤال‌های مشخص‌شده نیاز به اصلاح دارند.", "Correct the highlighted questions."))
    return render(request, "management_portal/v2/workspace_questionnaire.html", {
        "lang": lang, "case": case, "proposal": proposal, "assignment": assignment,
        "formset": formset,
    })


@staff_member_required(login_url="accounts:login")
def workspace_general_terms(request):
    lang = _lang(request)
    current = current_general_terms("fa")
    initial = {
        "title": current.title if current else "شرایط عمومی پیمان",
        "body": current.body if current else "",
        "change_note": "",
    }
    form = GeneralTermsRevisionForm(request.POST or None, initial=initial, lang=lang)
    if request.method == "POST" and form.is_valid():
        version = create_general_terms_version(
            title=form.cleaned_data["title"], body=form.cleaned_data["body"],
            change_note=form.cleaned_data["change_note"], actor=request.user, language="fa",
        )
        OperationalAudit.objects.create(
            actor=request.user, action="general_terms_version_created",
            target_type="general_terms_version", target_id=str(version.pk),
            summary=version.title, metadata={"version": version.number},
        )
        messages.success(request, _message(
            request,
            "نسخه تازه ثبت شد؛ قراردادهای قبلی بدون تغییر باقی ماندند.",
            "The new version was saved; existing contracts remain unchanged.",
        ))
        return redirect("management_portal:workspace_general_terms")
    return render(request, "management_portal/v2/workspace_general_terms.html", {
        "lang": lang, "current": current, "form": form,
        "versions": current.template.versions.all()[:20] if current else [],
    })


@staff_member_required(login_url="accounts:login")
@require_POST
def workspace_access_create(request, case_id):
    case = get_object_or_404(CustomerCase, pk=case_id)
    proposal = get_object_or_404(ContractProposal, customer_case=case, pk=request.POST.get("proposal_id"))
    form = WorkspaceAccessForm(request.POST, lang=_lang(request))
    if not form.is_valid():
        messages.error(request, _message(request, "اطلاعات دسترسی معتبر نیست.", "The access details are invalid."))
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
        return redirect("management_portal:workspace_detail", case_id=case.pk)
    raw_password = form.cleaned_data["password"] or generate_access_password()
    days = form.cleaned_data["expires_in_days"]
    expires_at = timezone.now() + timedelta(days=int(days)) if days else None
    try:
        grant = create_access_grant(
            proposal=proposal, authorized_phone=form.cleaned_data["authorized_phone"],
            raw_password=raw_password, actor=request.user, expires_at=expires_at,
        )
        delivery = None
        if form.cleaned_data["send_now"]:
            delivery = send_workspace_access(
                proposal=proposal, grant=grant,
                recipient_phone=form.cleaned_data["recipient_phone"], raw_password=raw_password,
                actor=request.user, absolute_base=request.build_absolute_uri("/"),
            )
    except ValidationError as exc:
        messages.error(request, _validation_text(exc))
        return redirect("management_portal:workspace_detail", case_id=case.pk)
    request.session[f"workspace_credentials_{case.pk}"] = {
        "phone": grant.authorized_phone,
        "recipient": form.cleaned_data["recipient_phone"],
        "password": raw_password,
        "url": workspace_access_url(proposal, absolute_base=request.build_absolute_uri("/")),
        "delivery_status": delivery.status if delivery else "not_sent",
    }
    OperationalAudit.objects.create(
        actor=request.user, action="workspace_access_created", target_type="contract_proposal",
        target_id=str(proposal.pk), summary=proposal.customer_name,
        metadata={"grant_id": grant.pk, "credential_version": grant.credential_version, "sms": bool(delivery)},
    )
    if delivery and delivery.status == "failed":
        messages.warning(request, _message(
            request,
            "دسترسی ساخته شد اما پیامک نرسید؛ اطلاعات یک‌بارنمایش را دستی ارسال کنید.",
            "Access was created, but SMS failed. Send the one-time credentials manually.",
        ))
    else:
        messages.success(request, _message(request, "دسترسی امن ساخته شد.", "Secure access was created."))
    return redirect("management_portal:workspace_detail", case_id=case.pk)


@staff_member_required(login_url="accounts:login")
@require_POST
def workspace_access_revoke(request, case_id, grant_id):
    case = get_object_or_404(CustomerCase, pk=case_id)
    grant = get_object_or_404(RoomAccessGrant, pk=grant_id, proposal__customer_case=case)
    revoke_access_grant(grant=grant, actor=request.user)
    OperationalAudit.objects.create(
        actor=request.user, action="workspace_access_revoked", target_type="room_access_grant",
        target_id=str(grant.pk), summary=grant.proposal.customer_name,
    )
    messages.success(request, _message(request, "دسترسی باطل شد.", "Access was revoked."))
    return redirect("management_portal:workspace_detail", case_id=case.pk)


@staff_member_required(login_url="accounts:login")
@require_POST
def workspace_publish(request, case_id):
    case = get_object_or_404(CustomerCase, pk=case_id)
    proposal = get_object_or_404(ContractProposal, customer_case=case, pk=request.POST.get("proposal_id"))
    try:
        version = publish_customer_workspace(proposal=proposal, actor=request.user)
    except ValidationError as exc:
        messages.error(request, _validation_text(exc))
    else:
        case.stage = "proposal"
        case.save(update_fields=("stage", "updated_at"))
        OperationalAudit.objects.create(
            actor=request.user, action="workspace_published", target_type="contract_proposal",
            target_id=str(proposal.pk), summary=proposal.project_title,
            metadata={"version": version.number},
        )
        messages.success(request, _message(
            request,
            "نسخه نهایی قفل و آماده مشاهده مشتری شد.",
            "The final version is locked and ready for the customer.",
        ))
    return redirect("management_portal:workspace_detail", case_id=case.pk)
