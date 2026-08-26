from django.conf import settings
from django.contrib import admin, messages
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .admin_exports import export_orders, export_results, export_tickets, mark_tickets_in_review, mark_tickets_resolved
from .models import (
    Attempt, AttemptResult, Certificate, Choice, Exam, ExamEntitlement,
    ExamSection, ExamVersion, IntegrityEvent, ManualPaymentSubmission, Order, PaymentTransaction,
    Question, Skill, SkillResult, SupportTicket,
)
from .services import PaymentVerificationError, approve_manual_payment


@admin.action(description="تأیید پرداخت‌های انتخاب‌شده و فعال‌سازی دسترسی")
def approve_manual_payments(modeladmin, request, queryset):
    approved = 0
    for submission in queryset.filter(status="pending").select_related("order__user", "order__exam"):
        try:
            with transaction.atomic():
                locked, order, created, applied = approve_manual_payment(
                    submission.pk,
                    reviewer=request.user,
                    review_note="تأیید دستی از پنل مدیریت جنگو",
                    automatic=False,
                )
                if not applied:
                    continue
            if created:
                send_mail(
                    "پرداخت شما تأیید و دسترسی آزمون فعال شد",
                    f"پرداخت سفارش {order.pk} تأیید شد. اکنون از حساب کاربری خود می‌توانید آزمون را شروع کنید:\n{settings.SITE_URL}/fa/account/",
                    settings.DEFAULT_FROM_EMAIL, [order.user.email], fail_silently=True,
                )
            approved += 1
        except PaymentVerificationError as exc:
            modeladmin.message_user(request, f"سفارش {submission.order_id}: {exc}", level=messages.ERROR)
    modeladmin.message_user(request, f"{approved} پرداخت تأیید شد.", level=messages.SUCCESS)


@admin.action(description="رد کردن پرداخت‌های انتخاب‌شده")
def reject_manual_payments(modeladmin, request, queryset):
    updated = queryset.filter(status="pending").update(
        status="rejected", reviewed_by=request.user, reviewed_at=timezone.now(), updated_at=timezone.now(),
    )
    modeladmin.message_user(request, f"{updated} پرداخت رد شد.", level=messages.WARNING)


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("title_en", "question_count", "duration_minutes", "price_irr", "is_active")
    list_filter = ("is_active", "language_mode")
    search_fields = ("title_fa", "title_en", "slug")
    prepopulated_fields = {"slug": ("title_en",)}


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "exam", "subtotal_display", "discount_percent", "amount_display", "status", "gateway", "created_at")
    list_filter = ("status", "gateway", "created_at")
    search_fields = ("id", "user__email", "exam__title_en")
    readonly_fields = ("id", "user", "exam", "subtotal_irr", "discount_irr", "discount_percent", "amount_irr", "gateway", "terms_version", "terms_accepted_at", "paid_at", "confirmation_email_sent_at", "created_at", "updated_at")
    actions = (export_orders,)

    @admin.display(description="مبلغ اولیه (ریال)", ordering="subtotal_irr")
    def subtotal_display(self, obj):
        return f"{obj.subtotal_irr:,}"

    @admin.display(description="مبلغ نهایی (ریال)", ordering="amount_irr")
    def amount_display(self, obj):
        return f"{obj.amount_irr:,}"


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("external_id", "order", "amount_display", "status", "verified_at")
    list_filter = ("status", "gateway")
    readonly_fields = ("order", "external_id", "amount_irr", "raw_response", "created_at", "verified_at")

    @admin.display(description="مبلغ (ریال)", ordering="amount_irr")
    def amount_display(self, obj):
        return f"{obj.amount_irr:,}"


@admin.register(ManualPaymentSubmission)
class ManualPaymentSubmissionAdmin(admin.ModelAdmin):
    list_display = ("reference_number", "order", "payer_name", "paid_at", "status", "created_at")
    list_filter = ("status", "paid_at", "created_at")
    search_fields = ("reference_number", "payer_name", "order__id", "order__user__email")
    readonly_fields = ("order", "payer_name", "reference_number", "paid_at", "note", "status", "reviewed_by", "reviewed_at", "created_at", "updated_at")
    actions = (approve_manual_payments, reject_manual_payments)
    change_list_template = "admin/assessments/manualpaymentsubmission/change_list.html"


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
    list_display = ("id", "user", "exam", "status", "completion_reason", "integrity_score", "started_at")
    list_filter = ("status", "exam")
    search_fields = ("id", "user__email")
    readonly_fields = (
        "id", "user", "exam", "version", "entitlement", "completion_reason", "selection_seed", "created_at", "updated_at",
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
    readonly_fields = ("attempt", "correct_count", "incorrect_count", "unanswered_count", "percentage", "level_code", "level_title_fa", "level_title_en", "summary_fa", "summary_en", "strengths", "weaknesses", "generated_at", "report_email_sent_at")
    inlines = (SkillResultInline,)
    actions = (export_results,)


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("verification_code", "holder_name", "result", "issued_at", "is_revoked")
    list_filter = ("is_revoked", "issued_at")
    search_fields = ("verification_code", "result__attempt__user__email")
    readonly_fields = ("id", "result", "holder_name", "verification_code", "issued_at")


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "category", "subject", "status", "created_at")
    list_filter = ("status", "category", "created_at")
    search_fields = ("user__email", "subject", "message", "order__id")
    readonly_fields = ("user", "order", "result", "category", "subject", "message", "created_at", "updated_at")
    actions = (export_tickets, mark_tickets_in_review, mark_tickets_resolved)
