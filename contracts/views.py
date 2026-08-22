import hashlib
import json
import secrets

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ImproperlyConfigured, PermissionDenied, ValidationError
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.cache import patch_cache_control
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.conf import settings
from management_portal.models import Customer, CustomerContact
from accounts.security import AttemptThrottle, client_address
from core.models import CompanyProfile
from crm_orders.models import CrmSpecialistDiscovery
from crm_orders.specialist import is_specialist_discovery_complete
from .forms import ClauseSelectionForm, ContractAccessForm, ContractReviewForm, ContractSettingsForm, DynamicQuestionnaireSectionForm, OtpRequestForm, ProposalForm
from .models import ContractAcceptance, ContractClause, ContractProposal, ContractReview, ContractRoomAcknowledgement, RoomAccessGrant, SpecialistAssignment
from .questionnaires import clean_answer, clean_section_answers, completion, merge_section_answers, normalize_schema, section_for_key
from .services import add_default_clauses, proposal_snapshot, publish_version
from .workspace_services import log_room_event


STATUS_LABELS_EN = {
    "draft": "Draft",
    "sent": "Sent",
    "review": "Customer feedback",
    "accepted": "Accepted",
    "expired": "Expired",
    "revoked": "Revoked",
}

QUESTIONNAIRE_AUTOSAVE_MAX_BYTES = 16 * 1024


def _request_language(request):
    return "en" if getattr(request, "LANGUAGE_CODE", "fa") == "en" else "fa"


def _copy(request, fa, en):
    return en if _request_language(request) == "en" else fa


def _status_label(proposal, language):
    return STATUS_LABELS_EN.get(proposal.status, proposal.status) if language == "en" else proposal.get_status_display()


def _require_contract_manager(request):
    if not request.user.is_superuser:
        raise PermissionDenied


def _version_phone(proposal, version):
    return str((version.snapshot or {}).get("customer_phone") or proposal.customer_phone)


def _session_key(version):
    return f"contract-access:{version.pk}"


def _session_grant(request, proposal, version):
    """Resolve a version-bound room session, including legacy phone sessions."""

    value = request.session.get(_session_key(version), "")
    if isinstance(value, str) and value.startswith("grant:"):
        try:
            _prefix, grant_id, credential_version = value.split(":", 2)
            grant = RoomAccessGrant.objects.get(
                pk=int(grant_id),
                proposal=proposal,
                credential_version=int(credential_version),
                is_active=True,
            )
        except (RoomAccessGrant.DoesNotExist, TypeError, ValueError):
            return None
        if not grant.is_available:
            return None
        return grant
    # Compatibility for links that were authenticated before per-room grants
    # existed. Once a proposal has any grant, only a grant session is valid.
    if not proposal.access_grants.exists() and value == _version_phone(proposal, version):
        return "legacy"
    return None


def _has_room_access(request, proposal, version):
    return _session_grant(request, proposal, version) is not None


def _session_phone(request, proposal, version):
    grant = _session_grant(request, proposal, version)
    return grant.authorized_phone if grant not in (None, "legacy") else _version_phone(proposal, version)


def _linked_discovery_state(proposal):
    """Return the linked CRM discovery and whether the contract may proceed."""
    assignment = SpecialistAssignment.objects.filter(proposal=proposal).select_related("version").first()
    if assignment:
        return assignment, completion(assignment.version.schema, assignment.answers)["is_complete"]
    if not proposal.crm_order_id:
        return None, True
    discovery = CrmSpecialistDiscovery.objects.filter(
        order_id=proposal.crm_order_id,
    ).first()
    complete = bool(
        discovery
        and discovery.status in {"submitted", "reviewed"}
        and is_specialist_discovery_complete(discovery)
    )
    return discovery, complete


def _discovery_evidence(proposal):
    assignment = SpecialistAssignment.objects.filter(proposal=proposal).select_related("version__template").first()
    if assignment:
        return {
            "assignment_id": assignment.pk,
            "template": assignment.version.template.slug,
            "template_version": assignment.version.number,
            "schema_hash": assignment.version.schema_hash,
            "status": assignment.status,
            "revision": assignment.revision,
            "answers": assignment.answers,
            "updated_at": assignment.updated_at.isoformat(),
        }
    discovery = CrmSpecialistDiscovery.objects.filter(
        order_id=proposal.crm_order_id,
    ).first() if proposal.crm_order_id else None
    if not discovery:
        return {}
    return {
        "order_id": proposal.crm_order_id,
        "tracking_code": proposal.crm_order.tracking_code,
        "status": discovery.status,
        "answers": discovery.answers,
        "updated_at": discovery.updated_at.isoformat(),
    }


def _questionnaire_locked(version):
    return hasattr(version, "acceptance") or version.room_acknowledgements.exists()


def _private_response(response):
    """Keep customer-room data out of browser and intermediary caches."""

    patch_cache_control(
        response,
        private=True,
        no_cache=True,
        no_store=True,
        must_revalidate=True,
        max_age=0,
    )
    response["Pragma"] = "no-cache"
    return response


def _questionnaire_section_index(schema, progress, section_key):
    completed = set(progress["completed_sections"])
    first_pending = next(
        (index for index, item in enumerate(schema) if item["key"] not in completed),
        len(schema),
    )
    current = next(
        (index for index, item in enumerate(schema) if item["key"] == section_key),
        None,
    )
    if current is None:
        raise Http404
    return current, first_pending


def _questionnaire_section_url(proposal, section_key):
    return reverse(
        "contracts:customer_questionnaire_section",
        args=[proposal.token, section_key],
    )


def _questionnaire_context(proposal, version, assignment, section, form, *, locked=False):
    schema = normalize_schema(assignment.version.schema)
    progress = completion(schema, assignment.answers)
    current_index, first_pending = _questionnaire_section_index(
        schema,
        progress,
        section["key"],
    )
    completed = set(progress["completed_sections"])
    navigation = []
    for index, item in enumerate(schema):
        navigation.append({
            "key": item["key"],
            "title": item["title"],
            "number": index + 1,
            "is_current": item["key"] == section["key"],
            "is_complete": item["key"] in completed,
            # Completed sections remain reviewable.  A new section is opened only
            # after every preceding required section has been completed.
            "is_available": locked or item["key"] in completed or index <= first_pending,
            "url": _questionnaire_section_url(proposal, item["key"]),
        })
    return {
        "proposal": proposal,
        "version": version,
        "assignment": assignment,
        "section": section,
        "section_number": current_index + 1,
        "section_count": len(schema),
        "form": form,
        "progress": progress,
        "navigation": navigation,
        "previous_section": schema[current_index - 1] if current_index else None,
        "next_section": schema[current_index + 1] if current_index + 1 < len(schema) else None,
        "locked": locked,
        "autosave_url": reverse("contracts:questionnaire_autosave", args=[proposal.token]),
    }


def _room_proposal_version(request, token, *, lock=False):
    proposal_queryset = ContractProposal.objects.select_for_update() if lock else ContractProposal.objects
    proposal = get_object_or_404(proposal_queryset, token=token)
    if not proposal.is_publicly_available or not proposal.current_version:
        raise Http404
    version_queryset = proposal.versions.select_for_update() if lock else proposal.versions
    version = version_queryset.get(number=proposal.current_version)
    if not _has_room_access(request, proposal, version):
        return proposal, version, None
    assignment_queryset = SpecialistAssignment.objects.select_for_update() if lock else SpecialistAssignment.objects
    assignment = get_object_or_404(assignment_queryset.select_related("version__template"), proposal=proposal)
    return proposal, version, assignment


def _manager_url(request, old_name, new_name, *args):
    namespace = getattr(getattr(request, "resolver_match", None), "namespace", "")
    return reverse(f"management_portal:{new_name}" if namespace == "management_portal" else f"contracts:{old_name}", args=args)


def _link_customer(proposal):
    customer = Customer.objects.filter(phone=proposal.customer_phone).first()
    if customer is None and proposal.customer_email:
        customer = Customer.objects.filter(email__iexact=proposal.customer_email).first()
    if customer is None:
        customer = Customer.objects.filter(name__iexact=proposal.customer_name).first()
    if customer is None:
        customer = Customer.objects.create(name=proposal.customer_name, kind="company", phone=proposal.customer_phone, email=proposal.customer_email)
    proposal.customer = customer
    CustomerContact.objects.get_or_create(customer=customer, name=proposal.customer_name, phone=proposal.customer_phone, email=proposal.customer_email, defaults={"is_primary": not customer.contacts.filter(is_primary=True).exists()})


@staff_member_required(login_url="accounts:login")
def proposal_list(request):
    _require_contract_manager(request)
    language = _request_language(request)
    rows = [{"item": item, "status_label": _status_label(item, language), "url": _manager_url(request, "proposal_detail", "contract_detail", item.pk)} for item in ContractProposal.objects.select_related("created_by")]
    return render(request, "contracts/proposal_list_v2.html", {"proposal_rows": rows, "create_url": _manager_url(request, "proposal_create", "contract_create"), "settings_url": _manager_url(request, "contract_settings", "contract_settings"), "lang": language})


@staff_member_required(login_url="accounts:login")
def contract_settings(request):
    _require_contract_manager(request)
    company = CompanyProfile.objects.first()
    if company is None:
        raise ImproperlyConfigured("Company profile must be configured before contract publishing.")
    language = _request_language(request)
    form = ContractSettingsForm(request.POST or None, instance=company, language=language)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _copy(request, "تنظیمات مجری قرارداد ذخیره شد؛ فقط نسخه‌های جدید از آن استفاده می‌کنند.", "Contractor settings saved; only new versions will use them."))
        return redirect(_manager_url(request, "proposal_list", "contract_list"))
    return render(request, "contracts/contract_settings.html", {"form": form, "list_url": _manager_url(request, "proposal_list", "contract_list"), "lang": language})


@staff_member_required(login_url="accounts:login")
@transaction.atomic
def proposal_create(request):
    _require_contract_manager(request)
    form = ProposalForm(request.POST or None, language=getattr(request, "LANGUAGE_CODE", "fa"))
    if request.method == "POST" and form.is_valid():
        proposal = form.save(commit=False)
        form.apply_assessment()
        proposal.created_by = request.user
        _link_customer(proposal)
        proposal.save()
        add_default_clauses(proposal)
        messages.success(request, _copy(request, "پیش‌نویس قرارداد ساخته شد؛ بندها را بررسی و سپس لینک را فعال کنید.", "Contract draft created. Review its clauses, then activate the customer link."))
        return redirect(_manager_url(request, "proposal_detail", "contract_detail", proposal.pk))
    return render(request, "contracts/proposal_form_v2.html", {"form": form, "assessment_data": form.assessment_data, "list_url": _manager_url(request, "proposal_list", "contract_list"), "lang": getattr(request, "LANGUAGE_CODE", "fa")})


@staff_member_required(login_url="accounts:login")
@transaction.atomic
def proposal_edit(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal, pk=proposal_id)
    if proposal.status not in {"draft", "revoked"}:
        raise PermissionDenied
    form = ProposalForm(request.POST or None, instance=proposal, language=getattr(request, "LANGUAGE_CODE", "fa"))
    if request.method == "POST" and form.is_valid():
        proposal = form.save(commit=False)
        if form.cleaned_data.get("needs_assessment"):
            form.apply_assessment()
        _link_customer(proposal)
        proposal.save()
        messages.success(request, _copy(request, "پیش‌نویس ذخیره شد. برای مشتری نسخه تازه بسازید.", "Draft saved. Create a new version before sharing it with the customer."))
        return redirect(_manager_url(request, "proposal_detail", "contract_detail", proposal.pk))
    return render(request, "contracts/proposal_form_v2.html", {"form": form, "assessment_data": form.assessment_data, "list_url": _manager_url(request, "proposal_list", "contract_list"), "proposal": proposal, "lang": getattr(request, "LANGUAGE_CODE", "fa")})


@staff_member_required(login_url="accounts:login")
def proposal_preview(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal.objects.prefetch_related("clauses"), pk=proposal_id)
    language = getattr(request, "LANGUAGE_CODE", "fa")
    return render(request, "contracts/proposal_preview.html", {
        "proposal": proposal,
        "snapshot": proposal_snapshot(proposal),
        "status_label": _status_label(proposal, language),
        "detail_url": _manager_url(request, "proposal_detail", "contract_detail", proposal.pk),
        "lang": language,
    })


@staff_member_required(login_url="accounts:login")
@require_POST
def proposal_revoke(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal, pk=proposal_id)
    if proposal.status == "accepted":
        raise PermissionDenied
    proposal.status = "revoked"
    proposal.save(update_fields=("status", "updated_at"))
    messages.success(request, _copy(request, "لینک مشتری غیرفعال شد؛ اطلاعات و نسخه‌ها حفظ شده‌اند.", "Customer link revoked; data and versions were preserved."))
    return redirect(_manager_url(request, "proposal_detail", "contract_detail", proposal.pk))


@staff_member_required(login_url="accounts:login")
@require_POST
def proposal_delete(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal, pk=proposal_id)
    if proposal.current_version or proposal.status not in {"draft", "revoked"}:
        raise PermissionDenied
    proposal.delete()
    messages.success(request, _copy(request, "پیش‌نویس بدون نسخه حذف شد.", "Unversioned draft deleted."))
    return redirect(_manager_url(request, "proposal_list", "contract_list"))


@staff_member_required(login_url="accounts:login")
def proposal_detail(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal.objects.prefetch_related("clauses", "versions"), pk=proposal_id)
    public_url = request.build_absolute_uri(reverse("contracts:public_contract", args=[proposal.token]))
    language = _request_language(request)
    return render(request, "contracts/proposal_detail_v2.html", {"proposal": proposal, "status_label": _status_label(proposal, language), "public_url": public_url, "list_url": _manager_url(request, "proposal_list", "contract_list"), "clauses_url": _manager_url(request, "proposal_clauses", "contract_clauses", proposal.pk), "publish_url": _manager_url(request, "proposal_publish", "contract_publish", proposal.pk), "edit_url": _manager_url(request, "proposal_edit", "contract_edit", proposal.pk), "preview_url": _manager_url(request, "proposal_preview", "contract_preview", proposal.pk), "revoke_url": _manager_url(request, "proposal_revoke", "contract_revoke", proposal.pk), "delete_url": _manager_url(request, "proposal_delete", "contract_delete", proposal.pk), "lang": language})


@staff_member_required(login_url="accounts:login")
@transaction.atomic
def proposal_clauses(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal.objects.prefetch_related("clauses"), pk=proposal_id)
    if proposal.status == "accepted":
        raise PermissionDenied
    form = ClauseSelectionForm(request.POST or None, proposal=proposal, language=getattr(request, "LANGUAGE_CODE", "fa"))
    if request.method == "POST" and form.is_valid():
        enabled = {int(value) for value in form.cleaned_data["enabled_clauses"]}
        proposal.clauses.update(is_enabled=False)
        proposal.clauses.filter(pk__in=enabled).update(is_enabled=True)
        title, body = form.cleaned_data["custom_title"].strip(), form.cleaned_data["custom_body"].strip()
        if title and body:
            position = (proposal.clauses.order_by("-position").values_list("position", flat=True).first() or 0) + 1
            ContractClause.objects.create(proposal=proposal, title=title, body=body, position=position)
        messages.success(request, _copy(request, "انتخاب بندها ذخیره شد. برای ارسال، نسخه جدید بسازید.", "Clause selection saved. Create a new version before sharing."))
        return redirect(_manager_url(request, "proposal_detail", "contract_detail", proposal.pk))
    return render(request, "contracts/proposal_clauses.html", {"proposal": proposal, "form": form, "detail_url": _manager_url(request, "proposal_detail", "contract_detail", proposal.pk), "lang": getattr(request, "LANGUAGE_CODE", "fa")})


@staff_member_required(login_url="accounts:login")
@require_POST
def proposal_publish(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal, pk=proposal_id)
    if proposal.status == "accepted":
        raise PermissionDenied
    try:
        version = publish_version(proposal, request.user)
    except ValidationError as exc:
        messages.error(
            request,
            _copy(
                request,
                "; ".join(exc.messages),
                "The contract is not ready to publish. Complete both terms and keep at least one clause enabled.",
            ),
        )
        return redirect(_manager_url(request, "proposal_detail", "contract_detail", proposal.pk))
    messages.success(request, _copy(request, f"نسخه {version.number} ثبت و لینک مشتری فعال شد.", f"Version {version.number} published and the customer link is active."))
    return redirect(_manager_url(request, "proposal_detail", "contract_detail", proposal.pk))


@never_cache
def public_contract(request, token):
    proposal = get_object_or_404(ContractProposal, token=token)
    if not proposal.is_publicly_available or not proposal.current_version:
        raise Http404
    version = proposal.versions.get(number=proposal.current_version)
    if not _has_room_access(request, proposal, version):
        return redirect("contracts:contract_access", token=token)
    discovery, discovery_complete = _linked_discovery_state(proposal)
    assignment = discovery if isinstance(discovery, SpecialistAssignment) else None
    acknowledgements = set(version.room_acknowledgements.values_list("document", flat=True))
    acceptance = getattr(version, "acceptance", None)
    ready_to_confirm = acceptance is None and acknowledgements == {"general", "private"} and discovery_complete
    return render(request, "contracts/contract_room.html", {
        "proposal": proposal,
        "version": version,
        "discovery": discovery,
        "assignment": assignment,
        "discovery_complete": discovery_complete,
        "questionnaire_progress": completion(assignment.version.schema, assignment.answers) if assignment else None,
        "acknowledgements": acknowledgements,
        "acceptance": acceptance,
        "ready_to_confirm": ready_to_confirm,
    })


def _first_questionnaire_section(schema, progress):
    completed = set(progress["completed_sections"])
    return next(
        (item for item in schema if item["key"] not in completed),
        schema[0],
    )


def _render_questionnaire(
    request,
    proposal,
    version,
    assignment,
    section,
    *,
    form=None,
    status=200,
    server_conflict=False,
):
    section_answers = (assignment.answers or {}).get(section["key"], {})
    if form is None:
        form = DynamicQuestionnaireSectionForm(
            section=section,
            initial=section_answers if isinstance(section_answers, dict) else {},
        )
    locked = _questionnaire_locked(version)
    if locked:
        for field in form.fields.values():
            field.disabled = True
    context = _questionnaire_context(
        proposal,
        version,
        assignment,
        section,
        form,
        locked=locked,
    )
    context["server_conflict"] = server_conflict
    response = render(
        request,
        "contracts/customer_questionnaire.html",
        context,
        status=status,
    )
    return _private_response(response)


def _questionnaire_access_redirect(proposal):
    return redirect("contracts:contract_access", token=proposal.token)


@never_cache
def customer_questionnaire(request, token, section_key=None):
    """Render and save one ordered section of the frozen specialist form."""

    if request.method not in {"GET", "POST"}:
        response = JsonResponse({"ok": False, "error": "method_not_allowed"}, status=405)
        response["Allow"] = "GET, POST"
        return _private_response(response)

    if request.method == "POST":
        with transaction.atomic():
            proposal, version, assignment = _room_proposal_version(
                request,
                token,
                lock=True,
            )
            if assignment is None:
                return _questionnaire_access_redirect(proposal)
            schema = normalize_schema(assignment.version.schema)
            progress = completion(schema, assignment.answers)
            if section_key is None:
                return redirect(
                    _questionnaire_section_url(
                        proposal,
                        _first_questionnaire_section(schema, progress)["key"],
                    )
                )
            try:
                section = section_for_key(schema, section_key)
            except ValidationError as exc:
                raise Http404 from exc
            current_index, first_pending = _questionnaire_section_index(
                schema,
                progress,
                section_key,
            )
            if (
                not progress["is_complete"]
                and section_key not in set(progress["completed_sections"])
                and current_index > first_pending
            ):
                messages.info(request, "ابتدا بخش قبلی فرم را کامل کنید.")
                return redirect(
                    _questionnaire_section_url(proposal, schema[first_pending]["key"])
                )
            if _questionnaire_locked(version):
                messages.info(
                    request,
                    "پس از ثبت مطالعه اسناد قرارداد، پاسخ‌های فرم فقط قابل مشاهده‌اند.",
                )
                return redirect(_questionnaire_section_url(proposal, section_key))

            form = DynamicQuestionnaireSectionForm(request.POST, section=section)
            try:
                submitted_revision = int(request.POST.get("revision", ""))
                if submitted_revision < 0:
                    raise ValueError
            except (TypeError, ValueError):
                submitted_revision = None
                form.add_error(None, "نسخه ذخیره فرم معتبر نیست؛ صفحه را تازه‌سازی کنید.")

            if submitted_revision is not None and submitted_revision != assignment.revision:
                form.add_error(
                    None,
                    "پاسخ‌های این فرم در دستگاه یا صفحه دیگری تغییر کرده‌اند. برای جلوگیری از حذف اطلاعات، صفحه را تازه‌سازی کنید.",
                )
                session_grant = _session_grant(request, proposal, version)
                log_room_event(
                    proposal,
                    "form_conflict",
                    request=request,
                    access_grant=session_grant if session_grant != "legacy" else None,
                    assignment=assignment,
                    metadata={
                        "section": section_key,
                        "client_revision": submitted_revision,
                        "server_revision": assignment.revision,
                        "source": "section_submit",
                    },
                )
                return _render_questionnaire(
                    request,
                    proposal,
                    version,
                    assignment,
                    section,
                    form=form,
                    status=409,
                    server_conflict=True,
                )

            if form.is_valid() and submitted_revision is not None:
                values = {
                    question["key"]: form.cleaned_data.get(question["key"])
                    for question in section["questions"]
                }
                try:
                    cleaned = clean_section_answers(
                        schema,
                        section_key,
                        values,
                        enforce_required=True,
                    )
                except ValidationError as exc:
                    form.add_error(None, "; ".join(exc.messages))
                    return _render_questionnaire(
                        request,
                        proposal,
                        version,
                        assignment,
                        section,
                        form=form,
                        status=400,
                    )
                was_complete = completion(schema, assignment.answers)["is_complete"]
                now = timezone.now()
                assignment.answers = merge_section_answers(
                    assignment.answers,
                    section_key,
                    cleaned,
                )
                assignment.progress = completion(schema, assignment.answers)
                assignment.revision += 1
                assignment.started_at = assignment.started_at or now
                assignment.last_saved_at = now
                assignment.status = "submitted" if assignment.progress["is_complete"] else "draft"
                assignment.submitted_at = (
                    assignment.submitted_at or now
                    if assignment.progress["is_complete"]
                    else None
                )
                assignment.reviewed_at = None
                assignment.save(update_fields=(
                    "answers",
                    "progress",
                    "revision",
                    "started_at",
                    "last_saved_at",
                    "status",
                    "submitted_at",
                    "reviewed_at",
                    "updated_at",
                ))
                session_grant = _session_grant(request, proposal, version)
                event_kwargs = {
                    "request": request,
                    "access_grant": session_grant if session_grant != "legacy" else None,
                    "assignment": assignment,
                }
                log_room_event(
                    proposal,
                    "form_saved",
                    metadata={
                        "section": section_key,
                        "revision": assignment.revision,
                        "source": "section_submit",
                    },
                    **event_kwargs,
                )
                if assignment.progress["is_complete"] and not was_complete:
                    log_room_event(
                        proposal,
                        "form_submitted",
                        metadata={"revision": assignment.revision},
                        **event_kwargs,
                    )
                    messages.success(
                        request,
                        "فرم تخصصی کامل و ذخیره شد. اکنون شرایط عمومی پیمان را بررسی کنید.",
                    )
                    return redirect("contracts:public_contract", token=proposal.token)

                next_index = current_index + 1
                messages.success(request, "پاسخ‌های این بخش با موفقیت ذخیره شد.")
                if next_index < len(schema):
                    return redirect(
                        _questionnaire_section_url(proposal, schema[next_index]["key"])
                    )
                return redirect("contracts:public_contract", token=proposal.token)

            return _render_questionnaire(
                request,
                proposal,
                version,
                assignment,
                section,
                form=form,
                status=400,
            )

    proposal, version, assignment = _room_proposal_version(request, token)
    if assignment is None:
        return _questionnaire_access_redirect(proposal)
    schema = normalize_schema(assignment.version.schema)
    progress = completion(schema, assignment.answers)
    if section_key is None:
        return redirect(
            _questionnaire_section_url(
                proposal,
                _first_questionnaire_section(schema, progress)["key"],
            )
        )
    try:
        section = section_for_key(schema, section_key)
    except ValidationError as exc:
        raise Http404 from exc
    current_index, first_pending = _questionnaire_section_index(
        schema,
        progress,
        section_key,
    )
    if (
        not _questionnaire_locked(version)
        and not progress["is_complete"]
        and section_key not in set(progress["completed_sections"])
        and current_index > first_pending
    ):
        messages.info(request, "ابتدا بخش قبلی فرم را کامل کنید.")
        return redirect(_questionnaire_section_url(proposal, schema[first_pending]["key"]))
    return _render_questionnaire(
        request,
        proposal,
        version,
        assignment,
        section,
    )


def _json_private(payload, *, status=200):
    return _private_response(JsonResponse(payload, status=status))


@never_cache
@require_POST
def questionnaire_autosave(request, token):
    """Persist one whitelisted answer with optimistic concurrency control."""

    try:
        content_length = int(request.META.get("CONTENT_LENGTH") or 0)
    except (TypeError, ValueError):
        content_length = 0
    if content_length > QUESTIONNAIRE_AUTOSAVE_MAX_BYTES:
        return _json_private(
            {"ok": False, "code": "payload_too_large", "message": "حجم پاسخ بیش از حد مجاز است."},
            status=413,
        )
    if request.content_type != "application/json":
        return _json_private(
            {"ok": False, "code": "invalid_content_type", "message": "نوع درخواست معتبر نیست."},
            status=415,
        )
    try:
        raw_body = request.body
        if len(raw_body) > QUESTIONNAIRE_AUTOSAVE_MAX_BYTES:
            raise OverflowError
        payload = json.loads(raw_body.decode("utf-8"))
    except OverflowError:
        return _json_private(
            {"ok": False, "code": "payload_too_large", "message": "حجم پاسخ بیش از حد مجاز است."},
            status=413,
        )
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _json_private(
            {"ok": False, "code": "invalid_json", "message": "ساختار درخواست معتبر نیست."},
            status=400,
        )

    allowed_keys = {"section", "field", "value", "revision"}
    if not isinstance(payload, dict) or set(payload) != allowed_keys:
        return _json_private(
            {"ok": False, "code": "invalid_payload", "message": "فیلدهای درخواست معتبر نیستند."},
            status=400,
        )
    section_key = payload.get("section")
    field_key = payload.get("field")
    revision = payload.get("revision")
    if (
        not isinstance(section_key, str)
        or not isinstance(field_key, str)
        or isinstance(revision, bool)
        or not isinstance(revision, int)
        or revision < 0
    ):
        return _json_private(
            {"ok": False, "code": "invalid_payload", "message": "فیلدهای درخواست معتبر نیستند."},
            status=400,
        )

    with transaction.atomic():
        proposal, version, assignment = _room_proposal_version(request, token, lock=True)
        if assignment is None:
            return _json_private({
                "ok": False,
                "code": "authentication_required",
                "message": "نشست شما پایان یافته است؛ دوباره وارد شوید.",
                "redirect": reverse("contracts:contract_access", args=[proposal.token]),
            }, status=401)
        schema = normalize_schema(assignment.version.schema)
        try:
            section = section_for_key(schema, section_key)
        except ValidationError:
            return _json_private(
                {"ok": False, "code": "unknown_section", "message": "بخش فرم معتبر نیست."},
                status=400,
            )
        question = next(
            (item for item in section["questions"] if item["key"] == field_key),
            None,
        )
        if question is None:
            return _json_private(
                {"ok": False, "code": "unknown_field", "message": "سؤال انتخاب‌شده معتبر نیست."},
                status=400,
            )
        existing_progress = completion(schema, assignment.answers)
        current_index, first_pending = _questionnaire_section_index(
            schema,
            existing_progress,
            section_key,
        )
        if (
            not existing_progress["is_complete"]
            and section_key not in set(existing_progress["completed_sections"])
            and current_index > first_pending
        ):
            return _json_private({
                "ok": False,
                "code": "section_locked",
                "message": "ابتدا بخش قبلی فرم را کامل کنید.",
            }, status=403)
        if _questionnaire_locked(version):
            return _json_private({
                "ok": False,
                "code": "questionnaire_locked",
                "message": "پس از ثبت مطالعه قرارداد، فرم فقط قابل مشاهده است.",
            }, status=423)
        if revision != assignment.revision:
            session_grant = _session_grant(request, proposal, version)
            log_room_event(
                proposal,
                "form_conflict",
                request=request,
                access_grant=session_grant if session_grant != "legacy" else None,
                assignment=assignment,
                metadata={
                    "section": section_key,
                    "field": field_key,
                    "client_revision": revision,
                    "server_revision": assignment.revision,
                    "source": "autosave",
                },
            )
            server_section = (assignment.answers or {}).get(section_key, {})
            return _json_private({
                "ok": False,
                "code": "revision_conflict",
                "message": "فرم در دستگاه دیگری تغییر کرده است؛ نسخه ذخیره‌شده را تازه‌سازی کنید.",
                "revision": assignment.revision,
                "server_value": server_section.get(field_key) if isinstance(server_section, dict) else None,
                "progress": completion(schema, assignment.answers),
            }, status=409)
        try:
            cleaned_value = clean_answer(
                question,
                payload.get("value"),
                enforce_required=False,
            )
        except ValidationError as exc:
            return _json_private({
                "ok": False,
                "code": "invalid_answer",
                "message": "; ".join(exc.messages),
            }, status=400)

        was_complete = existing_progress["is_complete"]
        section_answers = (assignment.answers or {}).get(section_key, {})
        section_answers = dict(section_answers) if isinstance(section_answers, dict) else {}
        section_answers[field_key] = cleaned_value
        assignment.answers = merge_section_answers(
            assignment.answers,
            section_key,
            section_answers,
        )
        assignment.progress = completion(schema, assignment.answers)
        now = timezone.now()
        assignment.revision += 1
        assignment.started_at = assignment.started_at or now
        assignment.last_saved_at = now
        assignment.status = "submitted" if assignment.progress["is_complete"] else "draft"
        assignment.submitted_at = (
            assignment.submitted_at or now
            if assignment.progress["is_complete"]
            else None
        )
        assignment.reviewed_at = None
        assignment.save(update_fields=(
            "answers",
            "progress",
            "revision",
            "started_at",
            "last_saved_at",
            "status",
            "submitted_at",
            "reviewed_at",
            "updated_at",
        ))
        session_grant = _session_grant(request, proposal, version)
        event_kwargs = {
            "request": request,
            "access_grant": session_grant if session_grant != "legacy" else None,
            "assignment": assignment,
        }
        log_room_event(
            proposal,
            "form_saved",
            metadata={
                "section": section_key,
                "field": field_key,
                "revision": assignment.revision,
                "source": "autosave",
            },
            **event_kwargs,
        )
        if assignment.progress["is_complete"] and not was_complete:
            log_room_event(
                proposal,
                "form_submitted",
                metadata={"revision": assignment.revision, "source": "autosave"},
                **event_kwargs,
            )

        return _json_private({
            "ok": True,
            "revision": assignment.revision,
            "saved_at": assignment.last_saved_at.isoformat(),
            "progress": assignment.progress,
        })


@never_cache
def contract_document(request, token, document=None):
    proposal = get_object_or_404(ContractProposal, token=token)
    if not proposal.is_publicly_available or not proposal.current_version:
        raise Http404
    version = proposal.versions.get(number=proposal.current_version)
    acknowledgements = set(version.room_acknowledgements.values_list("document", flat=True))
    if not _has_room_access(request, proposal, version):
        return redirect("contracts:contract_access", token=token)
    if document not in {"general", "private"}:
        return redirect("contracts:public_contract", token=token)
    _discovery, discovery_complete = _linked_discovery_state(proposal)
    # Reading a contract must not depend on completing the questionnaire.  The
    # customer can therefore review both documents early, while the POST view
    # below remains the sole authority for recording the ordered acknowledgements.
    can_acknowledge = discovery_complete and (
        document == "general" or "general" in acknowledgements
    )
    if not discovery_complete:
        acknowledgement_block_reason = (
            "این سند برای مطالعه در دسترس است. پس از تکمیل فرم نیازسنجی تخصصی، "
            "گزینه ثبت بررسی آن فعال می‌شود."
        )
    elif document == "private" and "general" not in acknowledgements:
        acknowledgement_block_reason = (
            "این سند برای مطالعه در دسترس است. برای ثبت بررسی شرایط خصوصی، "
            "ابتدا شرایط عمومی پیمان را بررسی و تأیید کنید."
        )
    else:
        acknowledgement_block_reason = ""
    if document in {"general", "private"}:
        event_key = f"contract-document-viewed:{version.pk}:{document}"
        if not request.session.get(event_key):
            session_grant = _session_grant(request, proposal, version)
            log_room_event(
                proposal,
                f"{document}_viewed",
                request=request,
                access_grant=session_grant if session_grant != "legacy" else None,
                metadata={"contract_version": version.number},
            )
            request.session[event_key] = True
        return render(request, "contracts/public_contract.html", {
            "proposal": proposal, "version": version, "snapshot": version.snapshot,
            "document": document, "terms": version.snapshot.get(f"{document}_terms", ""),
            "acknowledged": document in acknowledgements,
            "can_acknowledge": can_acknowledge,
            "acknowledgement_block_reason": acknowledgement_block_reason,
        })


@never_cache
@require_POST
def contract_acknowledge(request, token, document):
    proposal = get_object_or_404(ContractProposal, token=token)
    if document not in {"general", "private"} or not proposal.is_publicly_available or not proposal.current_version:
        raise Http404
    version = proposal.versions.get(number=proposal.current_version)
    if not _has_room_access(request, proposal, version):
        return redirect("contracts:contract_access", token=token)
    _discovery, discovery_complete = _linked_discovery_state(proposal)
    if not discovery_complete:
        messages.info(request, "ابتدا فرم نیازسنجی تخصصی را کامل کنید؛ سپس شرایط عمومی پیمان فعال می‌شود.")
        return redirect("contracts:public_contract", token=token)
    if request.POST.get("acknowledge") != "on":
        messages.error(request, "برای ثبت این مرحله، مطالعه کامل سند را تأیید کنید.")
        return redirect("contracts:contract_document", token=token, document=document)
    if not version.snapshot.get(f"{document}_terms"):
        raise Http404
    if document == "private" and not version.room_acknowledgements.filter(document="general").exists():
        messages.info(request, "ابتدا شرایط عمومی پیمان را بررسی و تأیید کنید.")
        return redirect("contracts:public_contract", token=token)
    ip = client_address(request)
    _acknowledgement, created = ContractRoomAcknowledgement.objects.get_or_create(
        version=version, document=document,
        defaults={"ip_hash": hashlib.sha256(ip.encode()).hexdigest() if ip else "", "user_agent": request.META.get("HTTP_USER_AGENT", "")[:240]},
    )
    if created:
        session_grant = _session_grant(request, proposal, version)
        log_room_event(
            proposal,
            f"{document}_accepted",
            request=request,
            access_grant=session_grant if session_grant != "legacy" else None,
            metadata={"contract_version": version.number},
        )
    messages.success(request, f"بررسی «{'شرایط عمومی پیمان' if document == 'general' else 'شرایط خصوصی پیمان'}» ثبت شد.")
    return redirect("contracts:public_contract", token=token)


@never_cache
@require_POST
def contract_logout(request, token):
    proposal = get_object_or_404(ContractProposal, token=token)
    if proposal.current_version:
        version = proposal.versions.filter(number=proposal.current_version).first()
        if version:
            session_grant = _session_grant(request, proposal, version)
            if session_grant:
                log_room_event(
                    proposal,
                    "logout",
                    request=request,
                    access_grant=session_grant if session_grant != "legacy" else None,
                    metadata={"contract_version": version.number},
                )
            request.session.pop(_session_key(version), None)
    request.session.modified = True
    messages.success(request, "از اتاق قرارداد خارج شدید.")
    return redirect("contracts:contract_access", token=token)


def _acceptance_version(request, token, *, lock=False):
    proposal_queryset = ContractProposal.objects.select_for_update() if lock else ContractProposal.objects
    proposal = get_object_or_404(proposal_queryset, token=token)
    if not proposal.is_publicly_available or not proposal.current_version:
        raise Http404
    version_queryset = proposal.versions.select_for_update() if lock else proposal.versions
    version = version_queryset.get(number=proposal.current_version)
    if not _has_room_access(request, proposal, version):
        messages.info(request, "نسخهٔ پرونده به‌روزرسانی شده است؛ برای ادامه، دوباره وارد پرونده شوید.")
        return proposal, version, "access"
    if hasattr(version, "acceptance"):
        return proposal, version, None
    acknowledgements = set(version.room_acknowledgements.values_list("document", flat=True))
    assignment_queryset = SpecialistAssignment.objects.select_for_update() if lock else SpecialistAssignment.objects
    assignment = assignment_queryset.select_related("version").filter(proposal=proposal).first()
    discovery = None
    if assignment:
        discovery = assignment
    elif proposal.crm_order_id:
        discovery_queryset = (
            CrmSpecialistDiscovery.objects.select_for_update()
            if lock else CrmSpecialistDiscovery.objects
        )
        discovery = discovery_queryset.filter(order_id=proposal.crm_order_id).first()
    if assignment:
        discovery_incomplete = not completion(assignment.version.schema, assignment.answers)["is_complete"]
    else:
        discovery_incomplete = bool(
            proposal.crm_order_id and (
                not discovery
                or discovery.status not in {"submitted", "reviewed"}
                or not is_specialist_discovery_complete(discovery)
            )
        )
    if acknowledgements != {"general", "private"} or discovery_incomplete:
        messages.info(request, "پیش از تأیید نهایی، فرم تخصصی و هر دو سند قرارداد را کامل کنید.")
        return proposal, version, "steps"
    return proposal, version, None


@never_cache
def contract_accept(request, token):
    proposal, version, blocked = _acceptance_version(request, token)
    if blocked == "access":
        return redirect("contracts:contract_access", token=token)
    if blocked:
        return redirect("contracts:public_contract", token=token)
    acceptance = getattr(version, "acceptance", None)
    return render(request, "contracts/contract_accept.html", {
        "proposal": proposal, "version": version, "acceptance": acceptance, "confirmation_form": OtpRequestForm(),
    })


@never_cache
@require_POST
@transaction.atomic
def contract_confirm(request, token):
    proposal, version, blocked = _acceptance_version(request, token, lock=True)
    if blocked == "access":
        return redirect("contracts:contract_access", token=token)
    if blocked:
        return redirect("contracts:public_contract", token=token)
    if hasattr(version, "acceptance"):
        return redirect("contracts:contract_accept", token=token)
    form = OtpRequestForm(request.POST)
    if not form.is_valid():
        messages.error(request, "برای ثبت تأیید نهایی، موافقت با نسخه را علامت بزنید.")
        return redirect("contracts:public_contract", token=token)
    discovery_snapshot = _discovery_evidence(proposal)
    evidence_payload = {
        "contract_snapshot_hash": version.snapshot_hash,
        "specialist_discovery": discovery_snapshot,
    }
    evidence_hash = hashlib.sha256(
        json.dumps(evidence_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    ip = client_address(request)
    ContractAcceptance.objects.create(
        version=version, verified_phone=_session_phone(request, proposal, version), provider_reference="",
        discovery_snapshot=discovery_snapshot, evidence_hash=evidence_hash,
        ip_hash=hashlib.sha256(ip.encode()).hexdigest() if ip else "", user_agent=request.META.get("HTTP_USER_AGENT", "")[:240],
    )
    proposal.status = "accepted"
    proposal.save(update_fields=["status", "updated_at"])
    session_grant = _session_grant(request, proposal, version)
    log_room_event(
        proposal,
        "final_accepted",
        request=request,
        access_grant=session_grant if session_grant != "legacy" else None,
        metadata={"contract_version": version.number, "evidence_hash": evidence_hash},
    )
    request.session.pop(_session_key(version), None)
    request.session.modified = True
    messages.success(request, "تأیید نهایی ثبت شد. از پرونده خارج شدید؛ تیم آرویون برای مرحله بعد با شما هماهنگ می‌شود.")
    return redirect("contracts:contract_access", token=token)


@never_cache
def contract_access(request, token):
    proposal = get_object_or_404(ContractProposal, token=token)
    if not proposal.is_publicly_available or not proposal.current_version:
        raise Http404
    version = proposal.versions.get(number=proposal.current_version)
    expected_phone = _version_phone(proposal, version)
    if _has_room_access(request, proposal, version):
        return redirect("contracts:public_contract", token=token)
    form = ContractAccessForm(request.POST or None)
    throttle = AttemptThrottle(
        "contract-access", request, token,
        getattr(settings, "CONTRACT_ACCESS_ATTEMPTS", 5),
        getattr(settings, "CONTRACT_ACCESS_WINDOW_SECONDS", 900),
    )
    if request.method == "POST" and throttle.blocked():
        form.add_error(None, "تلاش‌های ورود بیش از حد مجاز است؛ کمی بعد دوباره امتحان کنید.")
    elif request.method == "POST" and form.is_valid():
        phone = form.cleaned_data["phone"]
        raw_password = form.cleaned_data["password"]
        grant = None
        legacy_access = False
        with transaction.atomic():
            has_room_grants = proposal.access_grants.exists()
            if has_room_grants:
                grant = (
                    RoomAccessGrant.objects.select_for_update()
                    .filter(
                        proposal=proposal,
                        authorized_phone=phone,
                        is_active=True,
                    )
                    .order_by("-credential_version")
                    .first()
                )
                if not grant or not grant.is_available or not grant.check_password(raw_password):
                    grant = None
            else:
                configured_password = getattr(settings, "CONTRACT_ACCESS_PASSWORD", "")
                legacy_access = bool(
                    configured_password
                    and phone == expected_phone
                    and secrets.compare_digest(raw_password, configured_password)
                )

        if grant is None and not legacy_access:
            throttle.failure()
            log_room_event(
                proposal,
                "login_failed",
                request=request,
                metadata={"phone_last4": phone[-4:], "contract_version": version.number},
            )
            messages.error(request, "شماره همراه یا رمز ورود صحیح نیست.")
        else:
            throttle.success()
            if grant is not None:
                grant.last_login_at = timezone.now()
                grant.save(update_fields=("last_login_at", "updated_at"))
                request.session[_session_key(version)] = (
                    f"grant:{grant.pk}:{grant.credential_version}"
                )
                max_age = 7 * 24 * 60 * 60
                if grant.expires_at:
                    remaining = int((grant.expires_at - timezone.now()).total_seconds())
                    max_age = max(60, min(max_age, remaining))
                request.session.set_expiry(max_age)
                log_room_event(
                    proposal,
                    "login_succeeded",
                    request=request,
                    access_grant=grant,
                    metadata={"contract_version": version.number},
                )
            else:
                request.session[_session_key(version)] = expected_phone
                request.session.set_expiry(3600)
                log_room_event(
                    proposal,
                    "login_succeeded",
                    request=request,
                    metadata={"contract_version": version.number, "legacy": True},
                )
            return redirect("contracts:public_contract", token=token)
    elif request.method == "POST":
        throttle.failure()
    access_url = f"{settings.SITE_URL.rstrip('/')}{reverse('contracts:contract_access', args=[proposal.token])}"
    share_image_url = f"{settings.SITE_URL.rstrip('/')}{static('contracts/images/share-contract-room-v1.png')}"
    return render(request, "contracts/contract_access.html", {
        "proposal": proposal,
        "version": version,
        "form": form,
        # The access URL is deliberately the share target: legal documents stay
        # behind the phone/password gate while messengers still receive a rich card.
        "canonical_url": access_url,
        "share_image_url": share_image_url,
    })
