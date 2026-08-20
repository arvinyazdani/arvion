from django.contrib import admin

from .models import ContractAcceptance, ContractClause, ContractOtpChallenge, ContractProposal, ContractReview, ContractVersion


class ClauseInline(admin.StackedInline):
    model = ContractClause
    extra = 0


@admin.register(ContractProposal)
class ContractProposalAdmin(admin.ModelAdmin):
    list_display = ("project_title", "customer_name", "customer_phone", "status", "current_version", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("project_title", "customer_name", "customer_phone", "customer_email")
    readonly_fields = ("token", "current_version", "created_by", "created_at", "updated_at")
    inlines = (ClauseInline,)


@admin.register(ContractVersion)
class ContractVersionAdmin(admin.ModelAdmin):
    list_display = ("proposal", "number", "snapshot_hash", "created_by", "created_at")
    readonly_fields = ("proposal", "number", "snapshot", "snapshot_hash", "created_by", "created_at")

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(ContractReview)
class ContractReviewAdmin(admin.ModelAdmin):
    list_display = ("version", "reviewed_at")
    readonly_fields = ("version", "accepted_clause_ids", "rejected_clause_ids", "rejection_notes", "suggested_clause", "reviewed_at", "ip_hash", "user_agent")

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(ContractOtpChallenge)
class ContractOtpChallengeAdmin(admin.ModelAdmin):
    list_display = ("version", "phone", "attempts", "expires_at", "used_at", "created_at")
    exclude = ("code_hash",)
    readonly_fields = ("version", "phone", "provider_reference", "expires_at", "attempts", "used_at", "created_at")
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(ContractAcceptance)
class ContractAcceptanceAdmin(admin.ModelAdmin):
    list_display = ("version", "verified_phone", "accepted_at", "provider_reference")
    readonly_fields = ("version", "verified_phone", "provider_reference", "discovery_snapshot", "evidence_hash", "accepted_at", "ip_hash", "user_agent")
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
