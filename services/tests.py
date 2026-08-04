from django.test import TestCase
from django.urls import reverse

from .models import Service


class ServiceTests(TestCase):
    def test_inactive_service_is_not_public(self):
        service = Service.objects.create(title_fa="خدمت", title_en="Service", is_active=False)
        self.assertEqual(self.client.get(reverse("services:detail", args=[service.pk])).status_code, 404)
