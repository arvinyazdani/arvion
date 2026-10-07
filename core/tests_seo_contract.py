"""Anonymous search contracts over every emitted sitemap URL."""
import json
from html.parser import HTMLParser
from types import SimpleNamespace

from django.conf import settings
from django.contrib.sessions.models import Session
from django.test import Client, TestCase
from django.utils import translation
from django.utils import timezone
from django.urls import resolve

from assessments.models import Exam
from core.sitemaps import ExamSitemap, sitemaps
from blog.models import Post
from projects.models import DemoTemplate
from services.models import Service
from traffic.models import DailyVisitor, TrafficDay


class HeadParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.meta = {}
        self.links = []
        self.h1_count = 0
        self.title = ''
        self._in_title = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            self.meta[attrs.get('name') or attrs.get('property', '')] = attrs.get('content', '')
        elif tag == 'link':
            self.links.append(attrs)
        elif tag == 'h1':
            self.h1_count += 1
        elif tag == 'title':
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == 'title':
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


class WholeSitemapContractTests(TestCase):
    # These discovery wizards intentionally only have a Persian translation.
    FA_ONLY = {'crm_orders:create', 'clinic_orders:create'}
    # No duplicate title/description exceptions currently justified.
    UNIQUENESS_EXCEPTIONS = set()

    @classmethod
    def setUpTestData(cls):
        Service.objects.create(slug='seo-service', title_fa='خدمت آزمایشی',
                               title_en='Fixture service', short_description_fa='شرح خدمت آزمایشی',
                               short_description_en='Fixture service description')
        Post.objects.create(slug_fa='seo-post-fa', slug_en='seo-post-en',
                            title_fa='مقاله آزمایشی', title_en='Fixture article',
                            summary_fa='خلاصه مقاله آزمایشی', summary_en='Fixture article summary',
                            is_published=True, published_at=timezone.now())
        for category, _label in DemoTemplate.CATEGORY_CHOICES:
            for variant in range(2):
                DemoTemplate.objects.create(
                    slug=f'seo-{category}-{variant}', category=category,
                    title_fa=f'نمونه {category} {variant}', title_en=f'{category} sample {variant}',
                    tagline_fa=f'توضیح نمونه {category} {variant}',
                    tagline_en=f'{category} sample description {variant}',
                    fictional_brand_fa='برند فرضی', fictional_brand_en='Fictional brand',
                    style_key='minimal', default_features=['blog'])
        for slug in ('english-placement-a1-c1', 'python-django-professional'):
            Exam.objects.create(slug=slug, title_fa=f'آزمون {slug}', title_en=f'{slug} exam',
                                description_fa=f'شرح {slug}', description_en=f'About {slug}',
                                language_mode='bilingual', is_active=True)

    def setUp(self):
        translation.activate('fa')
        self.addCleanup(translation.deactivate_all)

    def pages(self):
        for sitemap_class in sitemaps.values():
            for entry in sitemap_class().get_urls(site=SimpleNamespace(domain='rvionai.com')):
                url = entry['location']
                path = url.removeprefix('https://rvionai.com')
                response = Client().get(path)
                yield url, path, response, HeadParser(response.content.decode())

    def test_entire_sitemap_is_public_indexable_canonical_and_reciprocal(self):
        pages = {url: (path, response, head) for url, path, response, head in self.pages()}
        for url, (path, response, head) in pages.items():
            with self.subTest(url=url):
                self.assertEqual(response.status_code, 200)
                self.assertNotIn('noindex', head.meta.get('robots', '').lower())
                self.assertNotIn('noindex', response.get('X-Robots-Tag', '').lower())
                self.assertEqual(head.h1_count, 1)
                self.assertTrue(head.title.strip())
                self.assertEqual([link['href'] for link in head.links if link.get('rel') == 'canonical'], [url])
                alternates = {link['hreflang']: link['href'] for link in head.links
                              if link.get('rel') == 'alternate' and 'hreflang' in link}
                with translation.override(path.split('/')[1]):
                    view_name = resolve(path).view_name
                if view_name in self.FA_ONLY:
                    self.assertEqual(set(alternates), {'fa', 'x-default'})
                else:
                    self.assertEqual(set(alternates), {'fa', 'en', 'x-default'})
                self.assertEqual(alternates['x-default'], alternates['fa'])
                for language, target in alternates.items():
                    self.assertIn(target, pages)
                    target_head = pages[target][2]
                    self.assertIn({'rel': 'alternate', 'hreflang': path.split('/')[1], 'href': url},
                                  target_head.links)

    def test_entire_sitemap_titles_and_descriptions_are_unique(self):
        seen = {'title': {}, 'description': {}}
        for url, _path, _response, head in self.pages():
            for kind, value in (('title', head.title), ('description', head.meta.get('description', ''))):
                value = ' '.join(value.split())
                with self.subTest(url=url, kind=kind):
                    self.assertTrue(value)
                    if url not in self.UNIQUENESS_EXCEPTIONS:
                        self.assertNotIn(value, seen[kind], f'Duplicate {kind}: {url} and {seen[kind].get(value)}')
                        seen[kind][value] = url

    def test_brand_is_localized_and_terms_have_their_own_description(self):
        for language, brand in (('fa', 'آرویون'), ('en', 'Rvion')):
            for path in ('/', '/company/', '/services/seo-service/', '/blog/seo-post-' + language + '/',
                         '/assessments/terms/'):
                with self.subTest(language=language, path=path):
                    response = Client().get('/' + language + path)
                    self.assertEqual(response.status_code, 200)
                    head = HeadParser(response.content.decode())
                    self.assertIn(brand, head.title)
                    self.assertEqual(head.meta['og:site_name'], brand)
                    self.assertTrue(head.meta['description'])


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
