from django.contrib import admin

from .models import Exam, ExamEntitlement, Order, PaymentTransaction


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
