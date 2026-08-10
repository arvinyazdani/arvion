from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class RvionUserAdmin(UserAdmin):
    list_display = ("email", "first_name", "last_name", "email_verified", "verification_email_count", "is_staff", "date_joined")
    list_filter = ("email_verified", "is_staff", "is_active", "preferred_language")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = UserAdmin.fieldsets + (("Rvion", {"fields": ("email_verified", "preferred_language")}),)
    actions = ("approve_accounts",)

    @admin.action(description="تأیید و فعال‌سازی حساب‌های انتخاب‌شده")
    def approve_accounts(self, request, queryset):
        count = queryset.filter(is_active=False).update(is_active=True, email_verified=True)
        self.message_user(request, f"{count} حساب تأیید و فعال شد.", messages.SUCCESS)
