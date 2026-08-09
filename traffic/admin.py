from django.contrib import admin

from .models import ActiveVisitor, DailyVisitor, TrafficDay


@admin.register(TrafficDay)
class TrafficDayAdmin(admin.ModelAdmin):
    list_display = ("date", "page_views", "unique_visitors")
    readonly_fields = ("date", "page_views", "unique_visitors")


@admin.register(ActiveVisitor)
class ActiveVisitorAdmin(admin.ModelAdmin):
    list_display = ("last_seen", "path", "is_authenticated")
    list_filter = ("is_authenticated",)
    readonly_fields = ("visitor_hash", "last_seen", "path", "is_authenticated")


@admin.register(DailyVisitor)
class DailyVisitorAdmin(admin.ModelAdmin):
    list_display = ("date", "visitor_hash")
    readonly_fields = ("date", "visitor_hash")
