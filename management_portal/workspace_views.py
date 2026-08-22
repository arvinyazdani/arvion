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
from django.db.models import Q
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
from contracts.models import ContractProposal, RoomAccessGrant
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

from .models import CustomerCase, OperationalAudit


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
            "customer", "general_terms_version", "created_by"
        )
        .prefetch_related(
            "access_grants", "room_deliveries", "room_events__actor",
            "versions__room_acknowledgements",
        )
        .exclude(status__in=("expired",))
        .order_by("-updated_at")
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


@staff_member_required(login_url="accounts:login")
def workspace_list(request):
    lang = _lang(request)
    query = request.GET.get("q", "").strip()
    state = request.GET.get("state", "all")
    cases = (
        CustomerCase.objects.select_related("customer", "owner")
        .prefetch_related("contract_proposals__access_grants")
        .order_by("-updated_at")
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
        cases = cases.filter(contract_proposals__isnull=True)
    elif state == "draft":
        cases = cases.filter(contract_proposals__status="draft")
    elif state == "sent":
        cases = cases.filter(contract_proposals__status__in=("sent", "review"))
    elif state == "accepted":
        cases = cases.filter(contract_proposals__status="accepted")

    rows = []
    for case in cases.distinct()[:150]:
        proposal = sorted(case.contract_proposals.all(), key=lambda item: item.updated_at, reverse=True)
        proposal = proposal[0] if proposal else None
        progress = workspace_progress(proposal) if proposal else None
        rows.append({"case": case, "proposal": proposal, "progress": progress})

    return render(request, "management_portal/v2/workspace_list.html", {
        "lang": lang,
        "rows": rows,
        "query": query,
        "state": state,
        "stats": {
            "all": CustomerCase.objects.count(),
            "not_started": CustomerCase.objects.filter(contract_proposals__isnull=True).count(),
            "active": ContractProposal.objects.filter(status__in=("draft", "sent", "review")).count(),
            "accepted": ContractProposal.objects.filter(status="accepted").count(),
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
    assignment = None
    progress = None
    if proposal:
        assignment = getattr(proposal, "specialist_assignment", None)
        progress = workspace_progress(proposal)
    credentials = request.session.pop(f"workspace_credentials_{case.pk}", None)
    documents = [
        {
            "document": document,
            "rows": _flatten_snapshot(document.snapshot),
            "revisions": document.revisions.all(),
        }
        for document in case.documents.all()
    ]
    return render(request, "management_portal/v2/workspace_detail.html", {
        "lang": lang,
        "case": case,
        "proposal": proposal,
        "assignment": assignment,
        "progress": progress,
        "documents": documents,
        "credentials": credentials,
        "contract_form": WorkspaceContractForm(instance=proposal, lang=lang) if proposal else None,
        "access_form": WorkspaceAccessForm(
            lang=lang,
            initial={"authorized_phone": case.phone or (case.customer.phone if case.customer else "")},
        ) if proposal else None,
        "access_url": workspace_access_url(proposal, absolute_base=request.build_absolute_uri("/")) if proposal else "",
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
        assignment = getattr(proposal, "specialist_assignment", None)
        return render(request, "management_portal/v2/workspace_detail.html", {
            "lang": _lang(request), "case": case, "proposal": proposal,
            "assignment": assignment, "progress": workspace_progress(proposal),
            "documents": [{"document": d, "rows": _flatten_snapshot(d.snapshot), "revisions": d.revisions.all()} for d in case.documents.prefetch_related("revisions")],
            "contract_form": form, "access_form": WorkspaceAccessForm(lang=_lang(request)),
            "access_url": workspace_access_url(proposal, absolute_base=request.build_absolute_uri("/")),
        }, status=400)
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
