from django.test import TestCase
from django.urls import reverse

from .models import Service


class ServiceTests(TestCase):
    def test_catalog_contains_five_complete_business_services(self):
        response = self.client.get(reverse("services:list") + "?lang=fa")
        self.assertEqual(Service.objects.filter(is_active=True).count(), 5)
        self.assertContains(response, "مشاوره محصول و پلتفرم آنلاین")
        self.assertContains(response, "ساخت وب‌اپلیکیشن و MVP اختصاصی")
        self.assertContains(response, "سه ماه پشتیبانی کدنویسی")

    def test_service_detail_shows_scope_process_and_prefilled_enquiry_link(self):
        service = Service.objects.get(slug="custom-web-application")
        response = self.client.get(service.get_absolute_url() + "?lang=fa")
        self.assertContains(response, "Backend و API امن")
        self.assertContains(response, "توسعه مرحله‌ای")
        self.assertContains(response, f"service={service.slug}")

    def test_inactive_service_is_not_public(self):
        service = Service.objects.create(
            slug="inactive", title_fa="خدمت", title_en="Service",
            short_description_fa="غیرفعال", short_description_en="Inactive", is_active=False,
        )
        self.assertEqual(self.client.get(service.get_absolute_url()).status_code, 404)
