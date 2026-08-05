import csv

from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone


def _safe_cell(value):
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@")):
        return f"'{text}"
    return text


def _csv_response(filename, headers, rows):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_safe_cell(value) for value in row])
    return response


@admin.action(description="Export selected orders as safe CSV")
def export_orders(modeladmin, request, queryset):
    rows = queryset.select_related("user", "exam").order_by("created_at").values_list(
        "id", "user__email", "exam__slug", "subtotal_irr", "discount_percent",
        "discount_irr", "amount_irr", "gateway", "status", "paid_at", "created_at",
    )
    return _csv_response(
        f"arvion-orders-{timezone.localdate().isoformat()}.csv",
        ("order_id", "user_email", "exam", "subtotal_irr", "discount_percent", "discount_irr", "final_irr", "gateway", "status", "paid_at", "created_at"),
        rows,
    )


@admin.action(description="Export selected results as safe CSV")
def export_results(modeladmin, request, queryset):
    rows = queryset.select_related("attempt__user", "attempt__exam", "attempt__version").order_by("generated_at").values_list(
        "id", "attempt__user__email", "attempt__exam__slug", "attempt__version__version",
        "percentage", "level_code", "correct_count", "incorrect_count", "unanswered_count",
        "attempt__integrity_score", "attempt__completion_reason", "generated_at",
    )
    return _csv_response(
        f"arvion-results-{timezone.localdate().isoformat()}.csv",
        ("result_id", "user_email", "exam", "version", "score", "level", "correct", "incorrect", "unanswered", "integrity", "completion_reason", "generated_at"),
        rows,
    )


@admin.action(description="Export selected support tickets as safe CSV")
def export_tickets(modeladmin, request, queryset):
    rows = queryset.select_related("user").order_by("created_at").values_list(
        "id", "user__email", "category", "status", "order_id", "result_id", "subject", "created_at", "updated_at",
    )
    return _csv_response(
        f"arvion-support-{timezone.localdate().isoformat()}.csv",
        ("ticket_id", "user_email", "category", "status", "order_id", "result_id", "subject", "created_at", "updated_at"),
        rows,
    )


@admin.action(description="Mark selected tickets as in review")
def mark_tickets_in_review(modeladmin, request, queryset):
    queryset.exclude(status="closed").update(status="in_review", updated_at=timezone.now())


@admin.action(description="Mark selected tickets as resolved")
def mark_tickets_resolved(modeladmin, request, queryset):
    queryset.exclude(status="closed").update(status="resolved", updated_at=timezone.now())
