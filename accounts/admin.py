from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import User


@admin.register(User)
class RvionUserAdmin(UserAdmin):
    change_list_template = "admin/accounts/user/change_list.html"
    list_display = ("email", "full_name", "account_status", "assigned_roles", "is_staff", "date_joined")
    list_filter = ("email_verified", "is_staff", "is_active", "preferred_language")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)
    filter_horizontal = ("groups",)
    fieldsets = (
        ("اطلاعات حساب", {"fields": ("username", "password", "email", "first_name", "last_name", "preferred_language")}),
        ("وضعیت و ورود", {"fields": ("is_active", "email_verified", "is_staff"), "description": "برای مشتری عادی فقط «فعال» و «ایمیل تأییدشده» کافی است. گزینه کارکنان فقط برای ورود به مدیریت است."}),
        ("نقش‌های آماده", {"fields": ("groups",), "description": "برای کارکنان یک یا چند نقش آماده انتخاب کنید؛ نیازی به تنظیم تک‌تک مجوزها نیست."}),
        ("سوابق", {"fields": ("last_login", "date_joined"), "classes": ("collapse",)}),
    )
    readonly_fields = ("last_login", "date_joined")
    actions = ("approve_accounts", "assign_sales_role", "assign_assessment_role", "assign_support_role", "remove_staff_access")

    @admin.display(description="نام")
    def full_name(self, obj):
        return obj.get_full_name() or "—"

    @admin.display(description="وضعیت")
    def account_status(self, obj):
        return "فعال" if obj.is_active else "منتظر تأیید"

    @admin.display(description="نقش‌ها")
    def assigned_roles(self, obj):
        labels = {"rvion_sales": "فروش", "rvion_assessments": "آزمون و پرداخت", "rvion_support": "پشتیبانی", "rvion_content": "محتوا", "rvion_analytics": "آمار"}
        return "، ".join(labels.get(name, name) for name in obj.groups.values_list("name", flat=True)) or "مشتری"

    @admin.action(description="تأیید و فعال‌سازی حساب‌های انتخاب‌شده")
    def approve_accounts(self, request, queryset):
        count = queryset.filter(is_active=False).update(is_active=True, email_verified=True)
        self.message_user(request, f"{count} حساب تأیید و فعال شد.", messages.SUCCESS)

    def _assign_role(self, request, queryset, role, label):
        group = Group.objects.filter(name=role).first()
        if not group:
            self.message_user(request, "نقش‌های آماده هنوز ساخته نشده‌اند.", messages.ERROR)
            return
        users = list(queryset)
        for user in users:
            user.groups.add(group)
        queryset.update(is_staff=True, is_active=True)
        self.message_user(request, f"نقش «{label}» به {len(users)} حساب داده شد.", messages.SUCCESS)

    @admin.action(description="دادن نقش فروش و CRM")
    def assign_sales_role(self, request, queryset): self._assign_role(request, queryset, "rvion_sales", "فروش و CRM")

    @admin.action(description="دادن نقش آزمون و تأیید پرداخت")
    def assign_assessment_role(self, request, queryset): self._assign_role(request, queryset, "rvion_assessments", "آزمون و پرداخت")

    @admin.action(description="دادن نقش پشتیبانی")
    def assign_support_role(self, request, queryset): self._assign_role(request, queryset, "rvion_support", "پشتیبانی")

    @admin.action(description="قطع دسترسی به پنل مدیریت")
    def remove_staff_access(self, request, queryset):
        count = queryset.filter(is_superuser=False).update(is_staff=False)
        self.message_user(request, f"دسترسی مدیریت {count} حساب قطع شد؛ حساب مشتری حذف یا غیرفعال نشده است.", messages.WARNING)
