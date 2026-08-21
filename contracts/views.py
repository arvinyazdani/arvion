import hashlib
import json
import secrets

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ImproperlyConfigured, PermissionDenied, ValidationError
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.conf import settings
from management_portal.models import Customer, CustomerContact
from accounts.security import AttemptThrottle, client_address
from core.models import CompanyProfile
from crm_orders.models import CrmSpecialistDiscovery
from crm_orders.specialist import is_specialist_discovery_complete
from .forms import ClauseSelectionForm, ContractAccessForm, ContractReviewForm, ContractSettingsForm, OtpRequestForm, ProposalForm
from .models import ContractAcceptance, ContractClause, ContractProposal, ContractReview, ContractRoomAcknowledgement
from .services import add_default_clauses, proposal_snapshot, publish_version


STATUS_LABELS_EN = {
    "draft": "Draft",
    "sent": "Sent",
    "review": "Customer feedback",
    "accepted": "Accepted",
    "expired": "Expired",
    "revoked": "Revoked",
}


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


def _linked_discovery_state(proposal):
    """Return the linked CRM discovery and whether the contract may proceed."""
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
    if request.session.get(f"contract-access:{version.pk}") != _version_phone(proposal, version):
        return redirect("contracts:contract_access", token=token)
    discovery, discovery_complete = _linked_discovery_state(proposal)
    acknowledgements = set(version.room_acknowledgements.values_list("document", flat=True))
    acceptance = getattr(version, "acceptance", None)
    ready_to_confirm = acceptance is None and acknowledgements == {"general", "private"} and (
        not proposal.crm_order_id or discovery_complete
    )
    return render(request, "contracts/contract_room.html", {"proposal": proposal, "version": version, "discovery": discovery, "discovery_complete": discovery_complete, "acknowledgements": acknowledgements, "acceptance": acceptance, "ready_to_confirm": ready_to_confirm})


@never_cache
def contract_document(request, token, document=None):
    proposal = get_object_or_404(ContractProposal, token=token)
    if not proposal.is_publicly_available or not proposal.current_version:
        raise Http404
    version = proposal.versions.get(number=proposal.current_version)
    acknowledgements = set(version.room_acknowledgements.values_list("document", flat=True))
    if request.session.get(f"contract-access:{version.pk}") != _version_phone(proposal, version):
        return redirect("contracts:contract_access", token=token)
    if document not in {"general", "private"}:
        return redirect("contracts:public_contract", token=token)
    _discovery, discovery_complete = _linked_discovery_state(proposal)
    if not discovery_complete:
        messages.info(request, "ابتدا فرم نیازسنجی تخصصی را کامل کنید؛ سپس شرایط عمومی پیمان فعال می‌شود.")
        return redirect("contracts:public_contract", token=token)
    if document == "private" and "general" not in acknowledgements:
        messages.info(request, "ابتدا شرایط عمومی پیمان را بررسی و تأیید کنید.")
        return redirect("contracts:public_contract", token=token)
    if document in {"general", "private"}:
        return render(request, "contracts/public_contract.html", {
            "proposal": proposal, "version": version, "snapshot": version.snapshot,
            "document": document, "terms": version.snapshot.get(f"{document}_terms", ""),
            "acknowledged": document in acknowledgements,
        })


@never_cache
@require_POST
def contract_acknowledge(request, token, document):
    proposal = get_object_or_404(ContractProposal, token=token)
    if document not in {"general", "private"} or not proposal.is_publicly_available or not proposal.current_version:
        raise Http404
    version = proposal.versions.get(number=proposal.current_version)
    if request.session.get(f"contract-access:{version.pk}") != _version_phone(proposal, version):
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
    ContractRoomAcknowledgement.objects.get_or_create(
        version=version, document=document,
        defaults={"ip_hash": hashlib.sha256(ip.encode()).hexdigest() if ip else "", "user_agent": request.META.get("HTTP_USER_AGENT", "")[:240]},
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
            request.session.pop(f"contract-access:{version.pk}", None)
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
    if request.session.get(f"contract-access:{version.pk}") != _version_phone(proposal, version):
        messages.info(request, "نسخهٔ پرونده به‌روزرسانی شده است؛ برای ادامه، دوباره وارد پرونده شوید.")
        return proposal, version, "access"
    if hasattr(version, "acceptance"):
        return proposal, version, None
    acknowledgements = set(version.room_acknowledgements.values_list("document", flat=True))
    discovery = None
    if proposal.crm_order_id:
        discovery_queryset = (
            CrmSpecialistDiscovery.objects.select_for_update()
            if lock else CrmSpecialistDiscovery.objects
        )
        discovery = discovery_queryset.filter(order_id=proposal.crm_order_id).first()
    if acknowledgements != {"general", "private"} or (
        proposal.crm_order_id and (
            not discovery
            or discovery.status not in {"submitted", "reviewed"}
            or not is_specialist_discovery_complete(discovery)
        )
    ):
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
        version=version, verified_phone=_version_phone(proposal, version), provider_reference="",
        discovery_snapshot=discovery_snapshot, evidence_hash=evidence_hash,
        ip_hash=hashlib.sha256(ip.encode()).hexdigest() if ip else "", user_agent=request.META.get("HTTP_USER_AGENT", "")[:240],
    )
    proposal.status = "accepted"
    proposal.save(update_fields=["status", "updated_at"])
    request.session.pop(f"contract-access:{version.pk}", None)
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
    if request.session.get(f"contract-access:{version.pk}") == expected_phone:
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
        configured_password = getattr(settings, "CONTRACT_ACCESS_PASSWORD", "")
        if not configured_password or form.cleaned_data["phone"] != expected_phone or not secrets.compare_digest(form.cleaned_data["password"], configured_password):
            throttle.failure()
            messages.error(request, "شماره همراه یا رمز ورود صحیح نیست.")
        else:
            throttle.success()
            request.session[f"contract-access:{version.pk}"] = expected_phone
            request.session.set_expiry(3600)
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
