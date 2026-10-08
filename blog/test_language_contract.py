"""Regression contracts for published posts with incomplete translations."""
from urllib.parse import parse_qs, urlsplit

from django.test import TestCase
from django.utils import timezone, translation

from blog.models import Post
from core.sitemaps import PostSitemap
from core.tests_seo_contract import HeadParser


class BlogLanguageContractTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.fa = Post.objects.create(
            slug_fa='persian-only', title_fa='مقاله فقط فارسی',
            summary_fa='خلاصه مستقل مقاله فارسی', body_fa='## بخش فارسی\n\nمتن نمونه.',
            is_published=True, published_at=timezone.now(),
        )
        cls.en = Post.objects.create(
            slug_en='english-only', title_en='English-only article',
            summary_en='An English-only summary.', body_en='## English section\n\nExample text.',
            is_published=True, published_at=timezone.now(),
        )
        cls.bilingual = Post.objects.create(
            slug_fa='both-fa', slug_en='both-en', title_fa='مقاله دوزبانه',
            title_en='Bilingual article', summary_fa='خلاصه دوزبانه', summary_en='Bilingual summary.',
            is_published=True, published_at=timezone.now(),
        )
        cls.bilingual.tags.add('selection')

    def setUp(self):
        translation.activate('fa')
        self.addCleanup(translation.deactivate_all)

    def test_lists_only_include_the_requested_translation(self):
        fa = self.client.get('/fa/blog/')
        en = self.client.get('/en/blog/')
        self.assertEqual({p.pk for p in fa.context['posts']}, {self.fa.pk, self.bilingual.pk})
        self.assertEqual({p.pk for p in en.context['posts']}, {self.en.pk, self.bilingual.pk})
        self.assertNotContains(en, '/en/blog/None/')
        self.assertNotContains(fa, '/fa/blog/None/')

    def test_slug_without_title_is_not_a_public_translation(self):
        invalid = Post.objects.create(slug_en='missing-title', title_en='',
                                      is_published=True, published_at=timezone.now())
        response = self.client.get('/en/blog/')
        self.assertNotIn(invalid.pk, {p.pk for p in response.context['posts']})
        self.assertEqual(self.client.get('/en/blog/missing-title/').status_code, 404)
        self.assertNotIn(('en', invalid), PostSitemap().items())

    def test_persian_only_detail_has_only_real_alternates_and_list_switch(self):
        response = self.client.get('/fa/blog/persian-only/')
        self.assertEqual(response.status_code, 200)
        head = HeadParser(response.content.decode())
        own = 'https://rvionai.com/fa/blog/persian-only/'
        self.assertEqual([x['href'] for x in head.links if x.get('rel') == 'canonical'], [own])
        self.assertEqual({x['hreflang']: x['href'] for x in head.links if 'hreflang' in x},
                         {'fa': own, 'x-default': own})
        self.assertEqual(response.context['language_switch_url'], '/en/blog/')
        self.assertNotContains(response, '/en/blog/None/')
        article = next(x for x in head.json_ld[0]['@graph'] if x['@type'] == 'BlogPosting')
        self.assertEqual(article['inLanguage'], 'fa')
        self.assertEqual(article['url'], own)

    def test_english_only_detail_uses_english_x_default_and_list_switch(self):
        response = self.client.get('/en/blog/english-only/')
        head = HeadParser(response.content.decode())
        own = 'https://rvionai.com/en/blog/english-only/'
        self.assertEqual({x['hreflang']: x['href'] for x in head.links if 'hreflang' in x},
                         {'en': own, 'x-default': own})
        self.assertEqual(response.context['language_switch_url'], '/fa/blog/')

    def test_other_language_cannot_resolve_the_persian_slug(self):
        self.assertEqual(self.client.get('/en/blog/persian-only/').status_code, 404)

    def test_bilingual_detail_keeps_its_real_translation_switch(self):
        response = self.client.get('/fa/blog/both-fa/')
        self.assertEqual(response.context['language_switch_url'], '/en/blog/both-en/')
        self.assertEqual(set(response.context['alternate_urls']), {'fa', 'en'})

    def test_no_fabricated_tag_on_an_untagged_article(self):
        response = self.client.get('/fa/blog/persian-only/')
        self.assertNotContains(response, '<span class="tag">Django</span>', html=True)

    def test_search_tag_and_pagination_preserve_both_filters(self):
        for number in range(11):
            post = Post.objects.create(slug_fa=f'paging-{number}', title_fa=f'فیلتر {number}',
                                       is_published=True, published_at=timezone.now())
            post.tags.add('selection')
        response = self.client.get('/fa/blog/', {'q': 'فیلتر', 'tag': 'selection'})
        self.assertEqual(response.context['paginator'].count, 11)
        # Pagination anchors are body elements, so inspect anchors separately.
        from html.parser import HTMLParser
        class Anchors(HTMLParser):
            def __init__(self, html):
                super().__init__(); self.links = []; self.feed(html)
            def handle_starttag(self, tag, attrs):
                if tag == 'a': self.links.append(dict(attrs).get('href', ''))
        next_query = next(parse_qs(urlsplit(href).query) for href in Anchors(response.content.decode()).links
                          if parse_qs(urlsplit(href).query).get('page') == ['2'])
        self.assertEqual(next_query, {'q': ['فیلتر'], 'tag': ['selection'], 'page': ['2']})
        self.assertEqual(self.client.get('/fa/blog/', {'q': 'no-match', 'tag': 'selection'}).context['paginator'].count, 0)

    def test_sitemap_only_has_languages_with_slug_and_title(self):
        entries = {(lang, post.pk) for lang, post in PostSitemap().items()}
        self.assertEqual(entries, {('fa', self.fa.pk), ('en', self.en.pk),
                                   ('fa', self.bilingual.pk), ('en', self.bilingual.pk)})
