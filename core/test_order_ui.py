from django.test import TestCase
from django.urls import reverse
from django.utils import translation
from services.models import Service
from projects.models import DemoTemplate
from core.templatetags.order_ui import order_phone


class OrderEntryUIContractTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)

    def test_service_ctas_and_addons_use_source_routes(self):
        from core.templatetags.order_ui import SERVICE_TOPICS
        for slug, topic in SERVICE_TOPICS.items():
            Service.objects.get_or_create(slug=slug, defaults={"title_fa": "خدمت", "title_en": "Service"})
            for lang in ("fa", "en"):
                page = self.client.get(f"/{lang}/services/{slug}/")
                self.assertContains(page, f'href="/{lang}/start/?type={topic}"')
                self.assertNotContains(page, f'href="/{lang}/contact/?service=')

    def test_home_category_fragments_exist_in_gallery_response(self):
        DemoTemplate.objects.create(slug="entry-fragment", category="corporate", title_fa="نمونه", title_en="Sample", style_key="minimal")
        for lang in ("fa", "en"):
            home = self.client.get(f"/{lang}/")
            gallery = self.client.get(f"/{lang}/projects/demos/")
            for item in home.context["home_demo_categories"]:
                self.assertEqual(item["url"].split("#")[-1], "demo-options")
                self.assertContains(gallery, 'id="demo-options"')

    def test_navigation_labels_agree_and_new_order_does_not_resume_draft(self):
        for lang, services, samples in (("fa", "خدمات", "نمونه‌ها"), ("en", "Services", "Samples")):
            html = self.client.get(f"/{lang}/").content.decode()
            header = html.split('id="site-nav"', 1)[1].split("</nav>", 1)[0]
            bar = html.split('<nav class="mobile-tabbar"', 1)[1].split("</nav>", 1)[0]
            for label in (services, samples):
                self.assertIn(label, header)
                self.assertIn(label, bar)
            self.assertIn(f'href="/{lang}/start/"', bar)
            self.assertIn(f'href="/{lang}/start/?consult=1"', header)
            self.assertNotIn(f'href="/{lang}/contact/"', header)

    def test_phone_links_normalize_existing_public_mobile(self):
        for value in ("09333021100", "۰۹۳۳۳۰۲۱۱۰۰", "+98 933 302 1100"):
            self.assertEqual(order_phone(value), "+989333021100")
        self.assertEqual(order_phone("invalid"), "")

    def test_home_article_first_card_is_lazy(self):
        from blog.models import Post
        from django.utils import timezone
        Post.objects.create(slug_fa="order-home-article", slug_en="order-home-article-en", title_fa="مقاله", title_en="Article", summary_fa="شرح", summary_en="Summary", is_published=True, published_at=timezone.now(), hero_image="blog/test.jpg")
        html = self.client.get("/fa/").content.decode()
        section = html.split('class="journal-home shell"', 1)[1].split("</section>", 1)[0]
        self.assertIn('loading="lazy"', section)
        self.assertNotIn('loading="eager"', section)

    def test_no_new_personal_identity_fields_before_final_form(self):
        for lang in ("fa", "en"):
            for topic in ("crm", "clinic", "other", "ecommerce"):
                html = self.client.get(f"/{lang}/start/?type={topic}").content.decode()
                for field in ("phone", "email", "contact_name", "business_name", "organization_name"):
                    self.assertNotIn(f'name="{field}"', html)
