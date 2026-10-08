"""Anonymous search contracts over every emitted sitemap URL."""
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace

from django.conf import settings
from django.contrib.sessions.models import Session
from django.test import Client, SimpleTestCase, TestCase
from django.utils import translation
from django.utils import timezone
from django.utils.html import escape
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
        self.related_links = []
        self._in_related_nav = False
        self.h1_count = 0
        self.title = ''
        self._in_title = False
        self.json_ld = []
        self._schema_buffer = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'nav' and 'data-seo-related' in attrs:
            self._in_related_nav = True
        elif tag == 'a' and self._in_related_nav:
            self.related_links.append(attrs.get('href', ''))
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
        if tag == 'nav':
            self._in_related_nav = False
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
    # Explicit single-language article exception, not a blog-wide hreflang waiver.
    PERSIAN_ONLY_POST_SLUGS = frozenset({'seo-persian-only'})
    # No duplicate title/description exceptions currently justified.
    UNIQUENESS_EXCEPTIONS = set()
    DEPLOYED_METADATA = json.loads(
        (Path(__file__).parent / 'fixtures' / 'seo_metadata_94c9c06.json').read_text()
    )['pages']
    TARGET_PATHS = frozenset(
        path for path in DEPLOYED_METADATA
        if ('/projects/demos/' in path and not path.endswith('/projects/demos/'))
        or ('/assessments/' in path and path.endswith('/about/'))
    )

    @classmethod
    def setUpTestData(cls):
        Service.objects.create(slug='seo-service', title_fa='خدمت آزمایشی',
                               title_en='Fixture service', short_description_fa='شرح خدمت آزمایشی',
                               short_description_en='Fixture service description')
        Post.objects.create(slug_fa='seo-post-fa', slug_en='seo-post-en',
                            title_fa='مقاله آزمایشی', title_en='Fixture article',
                            summary_fa='خلاصه مقاله آزمایشی', summary_en='Fixture article summary',
                            is_published=True, published_at=timezone.now())
        Post.objects.create(slug_fa='seo-persian-only',
                            title_fa='مقاله فارسی برای بررسی زبان',
                            summary_fa='خلاصه مستقل برای بررسی انتشار مقاله فارسی بدون ترجمه انگلیسی.',
                            body_fa='## عنوان بخش\n\nمتن آزمایشی مقاله.',
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
        # Public catalogue wording, not artificially shortened SEO fixtures.
        for slug, title_fa, title_en, description_fa, description_en in (
            ('english-placement-a1-c1', 'ارزیابی پیشرفته زبان انگلیسی مدرسان',
             'Advanced English Teacher Assessment',
             'غربالگری سطح بالای گرامر، دقت واژگانی، خواندن انتقادی، شنیدار، ویرایش و تحلیل آموزشی برای انتخاب مدرس.',
             'Advanced screening of grammar, lexical precision, critical reading, listening, editing, and pedagogical analysis for teacher selection.'),
            ('python-django-professional', 'ارزیابی تخصصی Python و Django',
             'Professional Python & Django Assessment',
             'سنجش عملی Python، حل مسئله، دیتابیس، تست، امنیت و استقرار پروژه‌های Django.',
             'A practical assessment of Python, problem solving, databases, testing, security, and Django deployment.'),
        ):
            Exam.objects.create(slug=slug, title_fa=title_fa, title_en=title_en,
                                description_fa=description_fa, description_en=description_en,
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
                persian_only_post = (view_name == 'blog:detail' and
                                     response.context['post'].slug_fa in self.PERSIAN_ONLY_POST_SLUGS)
                if view_name in self.FA_ONLY or persian_only_post:
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

    def test_generated_metadata_quality_entire_sitemap(self):
        seen_targets = set()
        for url, path, _response, head in self.pages():
            description = head.meta.get('description', '')
            for kind, value in (('title', head.title), ('description', description)):
                for marker in ('..', '.؛'):
                    with self.subTest(url=url, kind=kind, marker=marker):
                        self.assertNotIn(marker, value)
                with self.subTest(url=url, kind=kind, criterion='no_mid_text_ellipsis'):
                    self.assertNotRegex(value, r'…(?=.*\S)')
                with self.subTest(url=url, kind=kind, criterion='no_adjacent_repetition'):
                    self.assertNotRegex(value, r'(?iu)\b(\w+)\W+\1\b')
                    self.assertNotRegex(value, r'سایت\s+وب[\s\u200c-]?سایت')
            with self.subTest(url=url, criterion='title_length'):
                self.assertLessEqual(len(head.title), 60)
            if path in self.TARGET_PATHS:
                seen_targets.add(path)
                with self.subTest(url=url, criterion='description_length'):
                    self.assertGreaterEqual(len(description), 90)
                    self.assertLessEqual(len(description), 155)
        self.assertEqual(seen_targets, self.TARGET_PATHS)

    def test_every_non_target_live_page_metadata_is_byte_unchanged(self):
        self.assertEqual(len(self.TARGET_PATHS), 26)
        # The audit's production sitemap has no fixture-only services/posts/demos.
        # Restrict this assertion to that exact deployed URL inventory, while the
        # other whole-sitemap contracts also exercise all synthetic fixtures.
        expected_paths = set(self.DEPLOYED_METADATA) - self.TARGET_PATHS
        seen = set()
        for url, path, response, head in self.pages():
            if path not in expected_paths:
                continue
            seen.add(path)
            with self.subTest(url=url):
                self.assertEqual(response.status_code, 200)
                before = self.DEPLOYED_METADATA[path]
                self.assertEqual(head.title.encode('utf-8'), before['title'].encode('utf-8'))
                self.assertEqual(head.meta['description'].encode('utf-8'),
                                 before['description'].encode('utf-8'))
        self.assertEqual(seen, expected_paths)

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
                        self.assertIn(escape(item['name']), html)
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

    def test_contextual_links_have_matching_bilingual_indexable_targets(self):
        service_targets = {
            'corporate-website-design': ['parsa-advisory', 'linea-studio'],
            'ecommerce-platform': ['nava-market', 'sarvin-atelier'],
            'custom-web-application': ['roshna-clinic', 'ariana-academy', 'saffron-table'],
            'digital-product-consulting': [], 'maintenance-and-growth': [],
        }
        cases = [('', ['services/', 'crm/', 'assessments/'])]
        for slug, demos in service_targets.items():
            targets = [f'projects/demos/{demo}/' for demo in demos] or ['projects/demos/']
            if slug in ('custom-web-application', 'digital-product-consulting'):
                targets += ['crm/']
            cases.append((f'services/{slug}/', targets))
        for category, _label in DemoTemplate.CATEGORY_CHOICES:
            service = ('ecommerce-platform' if category in ('ecommerce', 'jewelry') else
                       'corporate-website-design' if category in ('corporate', 'portfolio') else
                       'custom-web-application')
            cases.append((f'projects/demos/seo-{category}-0/',
                          [f'services/{service}/', 'contact/']))
        for source, expected in cases:
            structures = []
            for lang in ('fa', 'en'):
                with self.subTest(source=source, lang=lang):
                    response = self.client.get(f'/{lang}/{source}')
                    self.assertEqual(response.status_code, 200)
                    links = HeadParser(response.content.decode()).related_links
                    self.assertEqual(links, [f'/{lang}/{target}' for target in expected])
                    structures.append([link.removeprefix(f'/{lang}/') for link in links])
                    for link in links:
                        target = self.client.get(link, follow=False)
                        self.assertEqual(target.status_code, 200, link)
                        self.assertNotIn('Location', target.headers, link)
                        self.assertNotIn('noindex', HeadParser(target.content.decode()).meta.get('robots', '').lower(), link)
                        self.assertNotIn('noindex', target.headers.get('X-Robots-Tag', '').lower(), link)
            self.assertEqual(structures[0], structures[1])

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


class MetadataCompositionTests(SimpleTestCase):
    def test_trailing_punctuation_is_owned_by_the_join_not_the_source(self):
        from core.templatetags.seo_metadata import demo_metadata
        for lang, brand in (('fa', 'آرویون'), ('en', 'Rvion')):
            demo = SimpleNamespace(
                category='corporate', category_label=('وب‌سایت شرکتی' if lang == 'fa' else 'Corporate website'),
                title_fa='شرکت خدمات حرفه‌ای', title_en='Professional services',
                tagline_fa='اعتمادسازی، خدمات و مسیر ساده تماس.؛ ',
                tagline_en='<b>Trust, services and a direct contact path.</b>.. ',
                fit_label='Unused fallback',
            )
            before = vars(demo).copy()
            result = demo_metadata(demo, lang, brand)
            self.assertEqual(vars(demo), before)
            self.assertLessEqual(len(result['title']), 60)
            self.assertTrue(90 <= len(result['description']) <= 155)
            self.assertNotIn('..', result['description'])
            self.assertNotIn('.؛', result['description'])
            self.assertNotIn('website website', result['title'])
            self.assertNotIn('سایت وب‌سایت', result['title'])
            self.assertNotIn('<b>', result['description'])

    def test_long_exam_copy_uses_the_complete_short_briefing_topic(self):
        from core.templatetags.seo_metadata import briefing_metadata
        exam = SimpleNamespace(
            title_fa='ارزیابی تخصصی Python و Django',
            title_en='Professional Python & Django Assessment',
            description_fa='توضیحات بسیار طولانی برای آزمون. ' * 20,
            description_en='A deliberately long complete source sentence. ' * 20,
        )
        before = vars(exam).copy()
        for lang, brand in (('fa', 'آرویون'), ('en', 'Rvion')):
            result = briefing_metadata(exam, lang, brand)
            self.assertLessEqual(len(result['title']), 60)
            self.assertTrue(90 <= len(result['description']) <= 155)
            self.assertNotIn('…', result['description'])
            self.assertNotIn('deliberately', result['description'])
            self.assertTrue(result['description'].endswith('.'))
        self.assertEqual(vars(exam), before)


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
