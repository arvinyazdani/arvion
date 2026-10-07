"""Read-only preparation checklist, separate from customer acknowledgements."""
from django.urls import reverse


STATUS_EN = {"draft": "Draft", "sent": "Published", "review": "Customer feedback",
             "accepted": "Accepted", "revoked": "Revoked", "expired": "Expired"}


def preparation(case, proposal, assignment, lang):
    def text(fa, en):
        return fa if lang == "fa" else en
    general = (proposal.general_terms_version.body if proposal and proposal.general_terms_version_id
               else proposal.general_terms if proposal else "")
    checks = [
        ("specialist", text("فرم تخصصی", "Specialist form"), bool(assignment and assignment.version.schema)),
        ("agreement", text("شرایط عمومی", "General terms"), bool(general.strip())),
        ("agreement", text("شرایط خصوصی و بندها", "Private terms and clauses"),
         bool(proposal and proposal.private_terms.strip() and any(c.is_enabled for c in proposal.clauses.all()))),
        ("access", text("دسترسی فعال", "Active customer access"),
         bool(proposal and any(g.is_available for g in proposal.access_grants.all()))),
    ]
    return [{"anchor": anchor, "title": title, "ready": ready,
             "label": text("آماده", "Ready") if ready else text("نیاز به تکمیل", "Needs preparation")}
            for anchor, title, ready in checks]


def source_links(case, user):
    """Only offer a source URL that still exists and the manager can open."""
    ct = case.source_content_type
    kinds = {"lead": ("lead", "leads.view_lead"), "crmorder": ("crm", "crm_orders.view_crmorder"),
             "clinicorder": ("clinic", "clinic_orders.view_clinicorder")}
    if not ct or ct.model not in kinds or not case.source_object_id:
        return {}
    kind, permission = kinds[ct.model]
    model = ct.model_class()
    if not (user.is_superuser or user.has_perm(permission)) or not model or not model.objects.filter(pk=case.source_object_id).exists():
        return {}
    return {"detail": reverse("management_portal:request_detail", args=[kind, case.source_object_id]),
            "export": reverse("management_portal:request_export", args=[kind, case.source_object_id]) + f"?workspace={case.pk}"}
