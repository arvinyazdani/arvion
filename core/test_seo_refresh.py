"""October owner-approved public metadata refresh (never article body edits)."""
from django.test import SimpleTestCase, TestCase
from django.utils import translation

from core.seo_copy import TITLES, DESCRIPTIONS, SERVICE_TITLES, SERVICE_DESCRIPTIONS
from core.tests_seo_contract import HeadParser
from services.models import Service
import re
from django.utils.html import strip_tags, escape
from django.utils import timezone
from blog.models import Post


class SearchCopyPolicyTests(SimpleTestCase):
    def test_editorial_lengths_and_uniqueness(self):
        for mapping, lower, upper in ((TITLES, 1, 60), (SERVICE_TITLES, 1, 60),
                                      (DESCRIPTIONS, 110, 160), (SERVICE_DESCRIPTIONS, 110, 160)):
            for language in range(2):
                seen = set()
                for route, pair in mapping.items():
                    value = pair[language]
                    if value is None:
                        continue
                    with self.subTest(route=route, language=language):
                        self.assertTrue(lower <= len(value) <= upper, (len(value), value))
                        self.assertNotIn(value, seen)
                        self.assertNotIn('..', value)
                        seen.add(value)


class SearchCopyRenderingTests(TestCase):
    def setUp(self):
        self.addCleanup(translation.deactivate_all)

    def test_service_metadata_is_specific_and_not_its_heading(self):
        for language in ('fa', 'en'):
            for service in Service.objects.filter(slug__in=SERVICE_TITLES):
                with self.subTest(service=service.slug, language=language):
                    response = self.client.get(f'/{language}/services/{service.slug}/')
                    head = HeadParser(response.content.decode())
                    self.assertEqual(head.title, SERVICE_TITLES[service.slug][language == 'en'])
                    self.assertNotEqual(head.title.split(' | ')[0], getattr(service, f'title_{language}'))
                    self.assertTrue(110 <= len(head.meta['description']) <= 160)
                    self.assertEqual(head.meta['description'], head.meta['og:description'])
                    self.assertEqual(head.title, head.meta['og:title'])
                    self.assertContains(response, getattr(service, f'title_{language}'))

    def test_organization_has_only_verified_alternate_names(self):
        head = HeadParser(self.client.get('/en/').content.decode())
        org = next(item for item in head.json_ld[0]['@graph'] if item['@type'] == 'Organization')
        self.assertEqual(org['alternateName'], ['آرویون', 'Rvion'])
        self.assertEqual(org['sameAs'], ['https://www.instagram.com/rvionai/'])

    def test_five_services_have_useful_bilingual_guides_and_five_visible_faqs(self):
        services = Service.objects.filter(slug__in=SERVICE_TITLES)
        self.assertEqual(services.count(), 5)
        for language in ('fa', 'en'):
            for service in services:
                with self.subTest(language=language, slug=service.slug):
                    response = self.client.get(f'/{language}/services/{service.slug}/')
                    html = response.content.decode()
                    main = re.search(r'<main\b[^>]*>(.*?)</main>', html, re.S).group(1)
                    main = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '', main, flags=re.S)
                    words = len(strip_tags(main).split())
                    self.assertTrue(800 <= words <= 1200, (service.slug, language, words))
                    faqs = response.context['service_faqs']
                    self.assertEqual(len(faqs), 5)
                    for question, answer in faqs:
                        self.assertContains(response, question)
                        self.assertContains(response, escape(answer))
                    self.assertEqual(HeadParser(html).h1_count, 1)

    def test_all_reviewed_articles_have_contextual_incoming_links_in_their_language(self):
        slugs = (
            'corporate-website-cost-1405', 'custom-website-vs-template',
            'custom-or-ready-made-crm', 'english-teacher-assessment',
            'clinic-website-design-online-booking', 'academy-website-structure-webinar',
            'enterprise-crm-development-cost-stages', 'django-interview-questions-with-short-answers',
            'custom-software-cost-us-2026-crm-accounting-b2b',
            'hire-django-freelancer-us-rates-2026', 'personal-accounting-economic-progress-raya',
        )
        for slug in slugs:
            persian_only = slug == slugs[-1]
            Post.objects.create(slug_fa=slug, slug_en=None if persian_only else slug,
                                title_fa=f'راهنمای {slug}', title_en=None if persian_only else f'Guide {slug}',
                                body_fa='متن راهنما', body_en=None if persian_only else 'Guide content',
                                is_published=True, published_at=timezone.now())
        for language in ('fa', 'en'):
            pages = ['', 'crm/', 'assessments/', 'projects/demos/']
            pages += [f'services/{slug}/' for slug in SERVICE_TITLES]
            rendered = ''.join(self.client.get(f'/{language}/{path}').content.decode() for path in pages)
            for slug in slugs[:-1] if language == 'en' else slugs:
                with self.subTest(language=language, slug=slug):
                    self.assertIn(f'href="/{language}/blog/{slug}/"', rendered)
            if language == 'en':
                self.assertNotIn(f'/en/blog/{slugs[-1]}/', rendered)
