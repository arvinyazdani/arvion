from django.contrib import admin
from .models import CompanyProfile, Page


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Identity", {"fields": ("brand_name", "legal_name_fa", "legal_name_en", "company_type_fa", "registration_number", "national_id", "established_date_fa")}),
        ("Management", {"fields": ("chief_executive_fa", "chief_executive_en")}),
        ("Contact", {"fields": ("phone", "postal_code", "address_fa", "address_en", "domain", "support_hours_fa", "support_hours_en")}),
    )

    def has_add_permission(self, request):
        return not CompanyProfile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """
    ادمین چندزبانه برای مدیریت صفحات ثابت.
    """
    list_display = ("slug", "get_title", "updated_at")
    search_fields = ("title_fa", "title_en", "slug")

    def get_title(self, obj):
        return obj.title_fa or obj.title_en
    get_title.short_description = "Title"
