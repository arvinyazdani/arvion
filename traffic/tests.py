from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import ActiveVisitor, DailyVisitor, TrafficDay


class TrafficMiddlewareTests(TestCase):
    def test_page_views_unique_visitors_and_online_are_recorded_without_ip(self):
        self.client.get(reverse("home"))
        self.client.get(reverse("about"))
        day = TrafficDay.objects.get(date=timezone.localdate())
        self.assertEqual(day.page_views, 2)
        self.assertEqual(day.unique_visitors, 1)
        self.assertEqual(DailyVisitor.objects.count(), 1)
        active = ActiveVisitor.objects.get()
        self.assertEqual(active.path, reverse("about"))
        self.assertFalse(any(field.name in {"ip", "ip_address"} for field in ActiveVisitor._meta.fields))

    def test_health_and_admin_are_excluded(self):
        self.client.get(reverse("health"))
        self.client.get(reverse("admin:index"))
        self.assertFalse(TrafficDay.objects.exists())

    def test_cleanup_removes_identifiers_not_aggregates(self):
        old = timezone.localdate() - timedelta(days=31)
        TrafficDay.objects.create(date=old, page_views=10, unique_visitors=4)
        DailyVisitor.objects.create(date=old, visitor_hash="a" * 64)
        ActiveVisitor.objects.create(visitor_hash="b" * 64, last_seen=timezone.now() - timedelta(days=2))
        from django.core.management import call_command
        call_command("cleanup_traffic_data")
        self.assertTrue(TrafficDay.objects.filter(date=old).exists())
        self.assertFalse(DailyVisitor.objects.exists())
        self.assertFalse(ActiveVisitor.objects.exists())
