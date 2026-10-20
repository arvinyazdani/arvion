from html.parser import HTMLParser

from django.test import TestCase

from projects.demo_policy import FEATURED_DEMO_SLUGS
from projects.models import DemoTemplate
from projects.models.demo import PUBLIC_DEMO_SLUGS


LEGACY_DEMO_SLUGS = (
    "orbit-shop",
    "roshna-clinic",
    "parsa-advisory",
    "northline-group",
    "nava-market",
    "ariana-academy",
    "sarvin-atelier",
    "atlas-profile",
    "saffron-table",
    "mora-cafe",
    "linea-studio",
)


class RobotsMetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.robots = []

    def handle_starttag(self, tag, attrs):
        if tag == "meta":
            attrs = dict(attrs)
            if attrs.get("name", "").lower() == "robots":
                self.robots.append(attrs.get("content", "").lower())


def robots_for(response):
    parser = RobotsMetaParser()
    parser.feed(response.content.decode())
    return parser.robots


class DemoRobotsPolicyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.demos = {}
        for index, slug in enumerate((*LEGACY_DEMO_SLUGS, *PUBLIC_DEMO_SLUGS)):
            cls.demos[slug], _ = DemoTemplate.objects.update_or_create(
                slug=slug,
                defaults=dict(
                    category="corporate",
                    title_fa=f"نمونه {index}",
                    title_en=f"Demo {index}",
                    tagline_fa="معرفی نمونه",
                    tagline_en="Demo introduction",
                    fictional_brand_fa="برند نمایشی",
                    fictional_brand_en="Sample brand",
                    style_key="modern",
                    default_features=[],
                    display_order=index,
                    is_active=True,
                ),
            )

    def test_every_legacy_preview_remains_available_but_noindexed_in_both_languages(self):
        for lang in ("fa", "en"):
            for slug in LEGACY_DEMO_SLUGS:
                with self.subTest(lang=lang, slug=slug):
                    response = self.client.get(f"/{lang}/projects/demos/{slug}/")
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(robots_for(response), ["noindex,follow"])
                    self.assertContains(response, 'rel="canonical"')

    def test_featured_previews_remain_indexable_and_kimia_stays_indexable(self):
        self.assertEqual(
            set(FEATURED_DEMO_SLUGS),
            {"ahanino-b2b-marketplace", "raya-personal-finance", "kimia-medical-crm"},
        )
        for lang in ("fa", "en"):
            for slug in PUBLIC_DEMO_SLUGS:
                with self.subTest(lang=lang, slug=slug):
                    response = self.client.get(f"/{lang}/projects/demos/{slug}/")
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(robots_for(response), ["index,follow,max-image-preview:large"])
            response = self.client.get(f"/{lang}/projects/demos/kimia-medical-crm/")
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("noindex", ",".join(robots_for(response)))

    def test_unlisted_active_demo_is_noindexed_without_removing_legacy_data(self):
        demo = DemoTemplate.objects.create(
            slug="legacy-unlisted-sample",
            category="corporate",
            title_fa="نمونهٔ قدیمی",
            title_en="Legacy sample",
            tagline_fa="معرفی",
            tagline_en="Introduction",
            fictional_brand_fa="برند نمایشی",
            fictional_brand_en="Sample brand",
            style_key="modern",
            is_active=True,
        )
        response = self.client.get(f"/fa/projects/demos/{demo.slug}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(robots_for(response), ["noindex,follow"])
        self.assertTrue(DemoTemplate.objects.filter(pk=demo.pk).exists())
