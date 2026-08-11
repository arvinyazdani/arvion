import hashlib

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .forms import ClauseSelectionForm, ContractReviewForm, ProposalForm
from .models import ContractClause, ContractProposal, ContractReview
from .services import add_default_clauses, publish_version


def _require_contract_manager(request):
    if not request.user.is_superuser:
        raise PermissionDenied


@staff_member_required(login_url="accounts:login")
def proposal_list(request):
    _require_contract_manager(request)
    return render(request, "contracts/proposal_list.html", {"proposals": ContractProposal.objects.select_related("created_by")})


@staff_member_required(login_url="accounts:login")
@transaction.atomic
def proposal_create(request):
    _require_contract_manager(request)
    form = ProposalForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        proposal = form.save(commit=False)
        proposal.created_by = request.user
        proposal.save()
        add_default_clauses(proposal)
        messages.success(request, "پیش‌نویس قرارداد ساخته شد؛ بندها را بررسی و سپس لینک را فعال کنید.")
        return redirect("contracts:proposal_detail", proposal_id=proposal.pk)
    return render(request, "contracts/proposal_form.html", {"form": form})


@staff_member_required(login_url="accounts:login")
def proposal_detail(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal.objects.prefetch_related("clauses", "versions"), pk=proposal_id)
    public_url = request.build_absolute_uri(reverse("contracts:public_contract", args=[proposal.token]))
    return render(request, "contracts/proposal_detail.html", {"proposal": proposal, "public_url": public_url})


@staff_member_required(login_url="accounts:login")
@transaction.atomic
def proposal_clauses(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal.objects.prefetch_related("clauses"), pk=proposal_id)
    if proposal.status == "accepted":
        raise PermissionDenied
    form = ClauseSelectionForm(request.POST or None, proposal=proposal)
    if request.method == "POST" and form.is_valid():
        enabled = {int(value) for value in form.cleaned_data["enabled_clauses"]}
        proposal.clauses.update(is_enabled=False)
        proposal.clauses.filter(pk__in=enabled).update(is_enabled=True)
        title, body = form.cleaned_data["custom_title"].strip(), form.cleaned_data["custom_body"].strip()
        if title and body:
            position = (proposal.clauses.order_by("-position").values_list("position", flat=True).first() or 0) + 1
            ContractClause.objects.create(proposal=proposal, title=title, body=body, position=position)
        messages.success(request, "انتخاب بندها ذخیره شد. برای ارسال، نسخه جدید بسازید.")
        return redirect("contracts:proposal_detail", proposal_id=proposal.pk)
    return render(request, "contracts/proposal_clauses.html", {"proposal": proposal, "form": form})


@staff_member_required(login_url="accounts:login")
@require_POST
def proposal_publish(request, proposal_id):
    _require_contract_manager(request)
    proposal = get_object_or_404(ContractProposal, pk=proposal_id)
    if proposal.status == "accepted":
        raise PermissionDenied
    version = publish_version(proposal, request.user)
    messages.success(request, f"نسخه {version.number} ثبت و لینک مشتری فعال شد.")
    return redirect("contracts:proposal_detail", proposal_id=proposal.pk)


@never_cache
def public_contract(request, token):
    proposal = get_object_or_404(ContractProposal, token=token)
    if not proposal.is_publicly_available or not proposal.current_version:
        raise Http404
    version = proposal.versions.get(number=proposal.current_version)
    existing = getattr(version, "review", None)
    form = ContractReviewForm(request.POST or None, version=version)
    if request.method == "POST" and not existing and form.is_valid():
        all_ids = {str(item["id"]) for item in version.snapshot["clauses"]}
        accepted = set(form.cleaned_data["accepted_clauses"])
        ip = request.META.get("REMOTE_ADDR", "")
        ContractReview.objects.create(
            version=version, accepted_clause_ids=sorted(accepted), rejected_clause_ids=sorted(all_ids - accepted),
            rejection_notes=form.cleaned_data["rejection_notes"].strip(), suggested_clause=form.cleaned_data["suggested_clause"].strip(),
            ip_hash=hashlib.sha256(ip.encode()).hexdigest() if ip else "",
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:240],
        )
        proposal.status = "review"
        proposal.save(update_fields=["status", "updated_at"])
        return redirect("contracts:public_contract", token=token)
    return render(request, "contracts/public_contract.html", {"proposal": proposal, "version": version, "snapshot": version.snapshot, "form": form, "review": existing})
