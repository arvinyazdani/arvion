from datetime import timedelta

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

DRAFT_RETENTION_DAYS = 7


def default_draft_expiry():
    return timezone.now() + timedelta(days=DRAFT_RETENTION_DAYS)


class FormDraft(models.Model):
    """A logged-in customer's saved, resumable, non-sensitive form draft.

    Deliberately mirrors the same safety boundary as the local (browser)
    draft mechanism: only categorical field selections and a frozen,
    bilingual demo-selection snapshot are ever stored here — never free
    text or contact information (name, phone, email, business name,
    website), and never `public_token`/`session_key`/`submission_token`.

    `leads.form_draft_service` is the only sanctioned way to write to this
    model; nothing should construct or save a `FormDraft` directly outside
    it, since that module is what enforces the field allowlist, the
    race-safe single-active-draft rule, and the expiry lifecycle.
    """

    FORM_TYPES = (
        ("leads_contact", "فرم تماس"),
    )
    STATUSES = (
        ("open", "باز"),
        ("submitting", "در حال ثبت"),
        ("submitted", "ثبت‌شده"),
        ("expired", "منقضی‌شده"),
    )
    ACTIVE_STATUSES = ("open", "submitting")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="form_drafts",
    )
    form_type = models.CharField(max_length=20, choices=FORM_TYPES, default="leads_contact")
    current_step = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(2)],
        help_text="Zero-based step index; leads_contact has 3 steps (0–2).",
    )
    fields = models.JSONField(default=dict, blank=True)
    demo_snapshot = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=12, choices=STATUSES, default="open", db_index=True)
    submitted_lead = models.ForeignKey(
        "leads.Lead", on_delete=models.SET_NULL, blank=True, null=True, related_name="source_form_drafts",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(default=default_draft_expiry, db_index=True)

    class Meta:
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=("owner", "status"), name="formdraft_owner_status_idx"),
            models.Index(fields=("status", "expires_at"), name="formdraft_status_expiry_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("owner", "form_type"),
                condition=models.Q(status__in=("open", "submitting")),
                name="unique_active_form_draft_per_owner_and_form_type",
            ),
        ]

    def __str__(self):
        return f"FormDraft(owner_id={self.owner_id}, form_type={self.form_type}, status={self.status})"
