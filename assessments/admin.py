from django.contrib import admin

from .models import (
    Attempt, AttemptResult, Certificate, Choice, Exam, ExamEntitlement,
    ExamSection, ExamVersion, IntegrityEvent, Order, PaymentTransaction,
    Question, Skill, SkillResult,
)


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("title_en", "question_count", "duration_minutes", "price_irr", "is_active")
    list_filter = ("is_active", "language_mode")
    search_fields = ("title_fa", "title_en", "slug")
    prepopulated_fields = {"slug": ("title_en",)}


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "exam", "amount_irr", "status", "gateway", "created_at")
    list_filter = ("status", "gateway", "created_at")
    search_fields = ("id", "user__email", "exam__title_en")
    readonly_fields = ("id", "user", "exam", "amount_irr", "gateway", "paid_at", "created_at", "updated_at")


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("external_id", "order", "amount_irr", "status", "verified_at")
    list_filter = ("status", "gateway")
    readonly_fields = ("order", "external_id", "amount_irr", "raw_response", "created_at", "verified_at")


@admin.register(ExamEntitlement)
class ExamEntitlementAdmin(admin.ModelAdmin):
    list_display = ("user", "exam", "attempts_remaining", "created_at", "expires_at")
    search_fields = ("user__email", "exam__title_en")
    readonly_fields = ("user", "exam", "order", "created_at")


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    fields = ("text_fa", "text_en", "is_correct", "explanation_fa", "explanation_en", "display_order")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("code", "exam", "title_en", "display_order")
    list_filter = ("exam",)


@admin.register(ExamVersion)
class ExamVersionAdmin(admin.ModelAdmin):
    list_display = ("exam", "version", "is_published", "published_at")
    list_filter = ("exam", "is_published")


@admin.register(ExamSection)
class ExamSectionAdmin(admin.ModelAdmin):
    list_display = ("code", "version", "question_count", "difficulty_distribution", "display_order")
    list_filter = ("version__exam",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "id", "version", "section", "question_type", "subskill", "content_group", "difficulty",
        "status", "exposure_count", "correct_response_count",
    )
    list_filter = ("version__exam", "version", "section", "question_type", "difficulty", "status")
    search_fields = ("prompt_fa", "prompt_en", "subskill", "content_group", "source_reference")
    readonly_fields = ("exposure_count", "correct_response_count", "created_at")
    inlines = (ChoiceInline,)


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "exam", "status", "integrity_score", "started_at")
    list_filter = ("status", "exam")
    search_fields = ("id", "user__email")
    readonly_fields = (
        "id", "user", "exam", "version", "entitlement", "selection_seed", "created_at", "updated_at",
    )


@admin.register(IntegrityEvent)
class IntegrityEventAdmin(admin.ModelAdmin):
    list_display = ("attempt", "event_type", "created_at")
    list_filter = ("event_type", "created_at")
    readonly_fields = ("attempt", "event_type", "metadata", "created_at")


class SkillResultInline(admin.TabularInline):
    model = SkillResult
    extra = 0
    readonly_fields = ("skill", "correct_count", "question_count", "percentage")


@admin.register(AttemptResult)
class AttemptResultAdmin(admin.ModelAdmin):
    list_display = ("attempt", "percentage", "level_code", "correct_count", "generated_at")
    list_filter = ("level_code", "generated_at")
    readonly_fields = ("attempt", "correct_count", "incorrect_count", "unanswered_count", "percentage", "level_code", "level_title_fa", "level_title_en", "summary_fa", "summary_en", "strengths", "weaknesses", "generated_at")
    inlines = (SkillResultInline,)


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("verification_code", "holder_name", "result", "issued_at", "is_revoked")
    list_filter = ("is_revoked", "issued_at")
    search_fields = ("verification_code", "result__attempt__user__email")
    readonly_fields = ("id", "result", "holder_name", "verification_code", "issued_at")
