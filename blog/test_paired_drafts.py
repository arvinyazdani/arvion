import io
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone, translation

from blog.models import Post
from blog.paired_drafts import load_paired_drafts
from blog.covers import cover_url
from core.tests_seo_contract import HeadParser


class PairedDraftTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)

    def run_import(self, *args):
        output = io.StringIO()
        call_command("import_blog_drafts", "--bundle", "international", *args, stdout=output)
        return output.getvalue()

    def test_three_records_five_languages_metadata_and_tables(self):
        self.run_import()
        self.assertEqual(Post.objects.count(), 3)
        self.assertEqual(Post.objects.exclude(slug_en__isnull=True).count(), 2)
        for draft in load_paired_drafts():
            post = Post.objects.get(slug_fa=draft.slug_fa)
            self.assertFalse(post.is_published)
            self.assertIsNone(post.published_at)
            for field, value in draft.values.items():
                self.assertEqual(getattr(post, field), value)
            if post.slug_en:
                self.assertIn('<table>', post.body_as_html())
                self.assertIn('<table>', post.body_as_html_en())
            for language in ("fa", "en"):
                if getattr(post, 'title_' + language):
                    self.assertLessEqual(len(getattr(post, 'title_' + language) + (' | آرویون' if language == 'fa' else ' | Rvion')), 60)
                    self.assertTrue(90 <= len(getattr(post, 'summary_' + language)) <= 155)

    def test_dry_run_repeat_and_publication_guard(self):
        self.run_import('--dry-run')
        self.assertEqual(Post.objects.count(), 0)
        self.run_import()
        before = list(Post.objects.values())
        self.run_import()
        self.assertEqual(before, list(Post.objects.values()))
        Post.objects.update(is_published=True, published_at=timezone.now(), title_fa='Owner title')
        before = list(Post.objects.values())
        self.run_import('--update')
        self.assertEqual(before, list(Post.objects.values()))

    def test_english_identity_collision_rolls_back(self):
        draft = next(d for d in load_paired_drafts() if 'slug_en' in d.values)
        Post.objects.create(slug_fa='owner', slug_en=draft.values['slug_en'])
        with self.assertRaises(CommandError):
            self.run_import()
        self.assertEqual(Post.objects.count(), 1)

    def test_drafts_do_not_leak_then_real_pair_canonical_schema_and_images(self):
        self.run_import()
        for post in Post.objects.all():
            for language in ('fa', 'en'):
                slug = getattr(post, 'slug_' + language) or post.slug_fa
                self.assertEqual(self.client.get(f'/{language}/blog/{slug}/').status_code, 404)
        Post.objects.update(is_published=True, published_at=timezone.now())  # test DB only
        for post in Post.objects.all():
            for language in ('fa', 'en'):
                slug = getattr(post, 'slug_' + language)
                if not slug:
                    self.assertEqual(self.client.get(f'/en/blog/{post.slug_fa}/').status_code, 404)
                    continue
                response = self.client.get(f'/{language}/blog/{slug}/')
                self.assertEqual(response.status_code, 200)
                head = HeadParser(response.content.decode())
                self.assertEqual(head.h1_count, 1)
                self.assertLessEqual(len(head.title), 60)
                self.assertTrue(90 <= len(head.meta['description']) <= 155)
                self.assertTrue(any(link.get('rel') == 'canonical' and link['href'].endswith(f'/{language}/blog/{slug}/') for link in head.links))
                graph = head.json_ld[0]['@graph']
                article = next(x for x in graph if x['@type'] == 'BlogPosting')
                self.assertEqual(article['inLanguage'], language)
                self.assertIn('author', article)
                self.assertIn(cover_url(post, language), article['image']['url'])
                self.assertContains(response, 'fetchpriority="high"')
                self.assertContains(response, f'src="{cover_url(post, language)}"')
                if not post.slug_en:
                    self.assertNotIn('hreflang="en"', response.content.decode().split('</head>')[0])

    def test_english_empty_listing_remains_noindex(self):
        self.run_import()
        self.assertContains(self.client.get('/en/blog/'), 'noindex')

    def test_incoming_links_only_after_publication(self):
        self.run_import()
        slug = load_paired_drafts()[0].slug_fa
        url = '/fa/blog/' + slug + '/'
        for route in ('/fa/', '/fa/crm/', '/fa/services/custom-web-application/', '/fa/projects/demos/'):
            self.assertNotContains(self.client.get(route), 'href="' + url + '"')
        Post.objects.update(is_published=True, published_at=timezone.now())
        for route in ('/fa/', '/fa/crm/', '/fa/services/custom-web-application/', '/fa/projects/demos/'):
            self.assertContains(self.client.get(route), 'href="' + url + '"')
        for language in ('fa', 'en'):
            self.assertContains(self.client.get('/' + language + '/'),
                                'src="/static/blog/covers/software-' + language + '-v1.jpg"')

    def test_cover_dimensions_weights_and_no_owner_image_override(self):
        from PIL import Image
        directory = Path(__file__).parent / 'static/blog/covers'
        self.assertEqual(len(list(directory.glob('*.jpg'))), 5)
        for path in directory.glob('*.jpg'):
            with Image.open(path) as image:
                self.assertEqual(image.size, (1200, 630))
            self.assertLess(path.stat().st_size, 150000)
        self.run_import()
        post = Post.objects.first()
        post.hero_image = 'articles/owner.jpg'
        self.assertEqual(cover_url(post, 'en'), '/media/articles/owner.jpg')

    def test_attach_dry_run_idempotence(self):
        self.run_import()
        with TemporaryDirectory() as media, self.settings(MEDIA_ROOT=media):
            call_command('attach_article_covers', '--bundle', 'international', '--dry-run', stdout=io.StringIO())
            self.assertEqual(list(Path(media).rglob('*.jpg')), [])
            call_command('attach_article_covers', '--bundle', 'international', stdout=io.StringIO())
            before = list(Post.objects.values_list('hero_image', flat=True))
            call_command('attach_article_covers', '--bundle', 'international', stdout=io.StringIO())
            self.assertEqual(before, list(Post.objects.values_list('hero_image', flat=True)))
            self.assertEqual(len(list(Path(media).rglob('*.jpg'))), 3)

    def test_published_fixture_links_and_sitemap_languages(self):
        from blog.test_import_drafts import BodyParser
        from core.sitemaps import PostSitemap
        self.run_import()
        Post.objects.update(is_published=True, published_at=timezone.now())
        entries = list(PostSitemap().items())
        self.assertEqual(len(entries), 5)
        titles, summaries = set(), set()
        for post in Post.objects.all():
            for language in ('fa', 'en'):
                if not getattr(post, 'slug_' + language):
                    continue
                title, summary = getattr(post, 'title_' + language), getattr(post, 'summary_' + language)
                self.assertNotIn(title, titles)
                self.assertNotIn(summary, summaries)
                titles.add(title)
                summaries.add(summary)
                body = post.body_as_html() if language == 'fa' else post.body_as_html_en()
                for href in BodyParser(body).links:
                    if href.startswith('/'):
                        self.assertEqual(self.client.get(href).status_code, 200, href)

    def test_pair_metadata_rejects_publication_and_incomplete_pairs(self):
        with TemporaryDirectory() as directory:
            source = Path(__file__).parent / 'international_drafts/11-custom-software-cost-us-en.md'
            text = source.read_text()
            path = Path(directory) / 'bad.md'
            # Test fixture writes, not repository/content edits.
            path.write_text(text)
            with self.assertRaisesMessage(ValueError, 'Persian edition'):
                load_paired_drafts(directory)
            path.write_text(text.replace('"draft-unreviewed"', '"published"'))
            with self.assertRaisesMessage(ValueError, 'publication status'):
                load_paired_drafts(directory)
