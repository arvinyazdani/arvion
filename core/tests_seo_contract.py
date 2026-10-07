"""Bounded search contracts; the site-wide metadata contract is still pending."""
from html.parser import HTMLParser
from types import SimpleNamespace

from django.conf import settings
from django.contrib.sessions.models import Session
from django.test import Client, TestCase
from django.utils import translation

from assessments.models import Exam
from core.sitemaps import ExamSitemap
from traffic.models import DailyVisitor, TrafficDay


class HeadParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.meta = {}
        self.links = []
        self.h1_count = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            self.meta[attrs.get('name', '')] = attrs.get('content', '')
        elif tag == 'link':
            self.links.append(attrs)
        elif tag == 'h1':
            self.h1_count += 1


class ExamSearchContractTests(TestCase):
    def setUp(self):
        translation.activate('fa')
        self.addCleanup(translation.deactivate_all)
        self.exam = Exam.objects.create(
            slug='seo-fixture', title_fa='آزمون آزمایشی سئو', title_en='SEO fixture assessment',
            description_fa='شرح آزمایشی', description_en='Fixture description',
            language_mode='bilingual', is_active=True,
        )
        self.inactive = Exam.objects.create(
            slug='seo-inactive', title_fa='آزمون غیرفعال', title_en='Inactive assessment',
            description_fa='شرح', description_en='Description', language_mode='bilingual',
            is_active=False,
        )

    def test_exam_sitemap_only_emits_active_public_briefings(self):
        sitemap = ExamSitemap()
        items = sitemap.items()
        expected = {f'/{lang}/assessments/{exam.slug}/about/'
                    for lang in ('fa', 'en') for exam in Exam.objects.filter(is_active=True)}
        self.assertEqual({sitemap.location(item) for item in items}, expected)
        self.assertTrue(all(sitemap.lastmod(item) == item[1].updated_at for item in items))
        self.assertFalse(any(item[1].pk == self.inactive.pk for item in items))

    def test_emitted_exam_urls_are_public_indexable_and_self_canonical(self):
        for entry in ExamSitemap().get_urls(site=SimpleNamespace(domain='rvionai.com')):
            url = entry['location']
            path = url.removeprefix('https://rvionai.com')
            with self.subTest(url=url):
                response = Client().get(path)
                self.assertEqual(response.status_code, 200)
                head = HeadParser(response.content.decode())
                self.assertNotIn('noindex', head.meta['robots'])
                self.assertEqual(head.h1_count, 1)
                self.assertEqual([link['href'] for link in head.links if link.get('rel') == 'canonical'], [url])
                alternates = {link['hreflang']: link['href'] for link in head.links
                              if link.get('rel') == 'alternate' and 'hreflang' in link}
                self.assertEqual(set(alternates), {'fa', 'en', 'x-default'})
                self.assertEqual(alternates['x-default'], alternates['fa'])
                for language in ('fa', 'en'):
                    self.assertEqual(alternates[language],
                                     f'https://rvionai.com/{language}/assessments/{self.exam.slug}/about/')

    def test_price_access_and_inactive_visibility_are_unchanged(self):
        self.assertEqual(self.client.get(f'/fa/assessments/{self.exam.slug}/').status_code, 302)
        self.assertEqual(self.client.get(f'/fa/assessments/{self.inactive.slug}/about/').status_code, 404)


class AnonymousTrafficCharacterizationTests(TestCase):
    """Diagnostic invariant, NOT acceptance for the blocked cookieless change."""

    def setUp(self):
        self.addCleanup(translation.deactivate_all)

    def test_analytics_itself_creates_session_even_without_language_write(self):
        # Isolate the second writer without changing production LanguageViewMixin.
        from unittest.mock import patch
        with patch('core.views.base.HomeView.dispatch', autospec=True) as dispatch:
            from django.http import HttpResponse
            dispatch.return_value = HttpResponse('anonymous public page')
            response = self.client.get('/fa/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(settings.SESSION_COOKIE_NAME, response.cookies)
        self.assertEqual(Session.objects.count(), 1)
        self.assertEqual(DailyVisitor.objects.count(), 1)
        self.assertEqual(TrafficDay.objects.get().unique_visitors, 1)
