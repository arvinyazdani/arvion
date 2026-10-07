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
        self.json_ld = []
        self._schema_buffer = None
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
        elif tag == 'script' and attrs.get('type') == 'application/ld+json':
            self._schema_buffer = ''

    def handle_endtag(self, tag):
        if tag == 'title':
            self._in_title = False
        elif tag == 'script' and self._schema_buffer is not None:
            self.json_ld.append(json.loads(self._schema_buffer))
            self._schema_buffer = None

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._schema_buffer is not None:
            self._schema_buffer += data


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

    def test_schema_is_one_graph_with_unique_ids_and_absolute_local_urls(self):
        def check_urls(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in {'@id', 'url', 'item', 'logo', 'image'} and isinstance(child, str):
                        self.assertTrue(child.startswith('https://rvionai.com/'), child)
                    check_urls(child)
            elif isinstance(value, list):
                for child in value:
                    check_urls(child)

        for url, path, response, head in self.pages():
            with self.subTest(url=url):
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(head.json_ld), 1)
                graph = head.json_ld[0]['@graph']
                ids = [node['@id'] for node in graph]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertEqual(sum(node['@type'] == 'Organization' for node in graph), 1)
                self.assertEqual(sum(node['@type'] == 'WebSite' for node in graph), 1)
                check_urls(graph)
                self.assertNotIn('aggregateRating', str(graph))
                self.assertNotIn('Offer', str(graph))
                if path not in {'/fa/', '/en/'}:
                    breadcrumb = next(node for node in graph if node['@type'] == 'BreadcrumbList')
                    html = response.content.decode()
                    self.assertIn('class="shell seo-breadcrumbs"', html)
                    self.assertIn('aria-current="page"', html)
                    for item in breadcrumb['itemListElement']:
                        self.assertIn(item['name'], html)
                if '/assessments/' in path:
                    self.assertNotIn('Course', str(graph))

    def test_schema_uses_profile_and_escapes_script_breakout(self):
        from core.models import CompanyProfile
        # The profile seeded by migrations is public company data, not customer PII.
        company = CompanyProfile.objects.first()
        self.assertIsNotNone(company)
        company.phone = '+980000000000'
        company.legal_name_en = '</script><script>alert("test")</script>'
        company.save()
        response = self.client.get('/en/company/')
        head = HeadParser(response.content.decode())
        org = next(node for node in head.json_ld[0]['@graph'] if node['@type'] == 'Organization')
        self.assertEqual(org['telephone'], company.phone)
        self.assertEqual(org['legalName'], company.legal_name_en)
        self.assertNotIn('</script><script>alert', response.content.decode())
        self.assertNotIn('sameAs', org)

    def test_private_account_does_not_receive_public_schema(self):
        response = self.client.get('/fa/account/login/')
        self.assertEqual(HeadParser(response.content.decode()).json_ld, [])

    def test_organization_phone_normalization_is_render_only(self):
        from core.models import CompanyProfile
        company = CompanyProfile.objects.first()
        for stored, expected in (
            ('09333021100', '+989333021100'),
            ('+989333021100', '+989333021100'),
            ('', None),
        ):
            with self.subTest(phone=stored):
                # Blank represents a legacy/incomplete profile; the model's
                # current full_clean correctly disallows saving it via forms.
                CompanyProfile.objects.filter(pk=company.pk).update(phone=stored)
                response = self.client.get('/fa/company/')
                graph = HeadParser(response.content.decode()).json_ld[0]['@graph']
                org = next(node for node in graph if node['@type'] == 'Organization')
                self.assertEqual(org.get('telephone'), expected)
                if expected is None:
                    self.assertNotIn('telephone', org)
                else:
                    self.assertContains(response, stored)
                company.refresh_from_db()
                self.assertEqual(company.phone, stored)

    def test_home_font_preload_is_limited_to_persian_above_fold_fonts(self):
        response = self.client.get('/fa/')
        html = response.content.decode()
        for weight in ('Regular', 'Bold', 'Black'):
            self.assertIn(f'core/fonts/Vazirmatn-{weight}.woff2', html)
        self.assertEqual(html.count('as="font"'), 3)
        self.assertLess(html.index('as="font"'), html.index('core/css/tokens.css'))
        for path in ('/en/', '/fa/blog/', '/fa/services/seo-service/'):
            self.assertNotContains(self.client.get(path), 'as="font"')

    def test_page_specific_types_and_profile_absence_are_truthful(self):
        from core.models import CompanyProfile
        CompanyProfile.objects.all().delete()
        for path, expected in (
            ('/fa/services/seo-service/', 'Service'), ('/en/crm/', 'Service'),
            ('/fa/assessments/english-placement-a1-c1/about/', 'WebPage'),
        ):
            response = self.client.get(path)
            graph = HeadParser(response.content.decode()).json_ld[0]['@graph']
            self.assertIn(expected, [node['@type'] for node in graph])
            organization = next(node for node in graph if node['@type'] == 'Organization')
            self.assertNotIn('telephone', organization)
            self.assertNotIn('address', organization)
            self.assertNotIn('identifier', organization)
            if '/assessments/' in path:
                self.assertEqual({node['@type'] for node in graph},
                                 {'Organization', 'WebSite', 'WebPage', 'BreadcrumbList'})


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
