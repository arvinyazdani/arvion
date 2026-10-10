"""Public article contracts; content and SEO ownership stay with existing models."""
from django.test import TestCase
from django.utils import timezone, translation
from blog.models import Post
from blog.presentation import reader_content
from pathlib import Path
from django.conf import settings


class ArticleListTests(TestCase):
    def setUp(self):
        translation.activate('fa')
        self.addCleanup(translation.deactivate_all)
        self.post = Post.objects.create(title_fa='راهنمای انتخاب', title_en='Choosing well',
            slug_fa='choice', slug_en='choice', summary_fa='خلاصه راهنما', summary_en='Guide summary',
            body_fa='عبارت فقط در متن', body_en='body-only-needle',
            is_published=True, published_at=timezone.now())
        self.post.tags.add('Design')

    def test_count_search_tags_not_body_and_local_language(self):
        response = self.client.get('/fa/blog/')
        self.assertEqual(response.context['article_tags'], [{'name': 'Design', 'count': 1}])
        self.assertEqual(self.client.get('/en/blog/?q=Design').context['paginator'].count, 1)
        self.assertEqual(self.client.get('/en/blog/?q=body-only-needle').context['paginator'].count, 0)
        self.assertEqual(self.client.get('/en/blog/?q=راهنمای').context['paginator'].count, 0)

    def test_latest_badge_only_unfiltered_first_page(self):
        self.assertContains(self.client.get('/fa/blog/'), 'ar-badge')
        for query in ('?q=راهنمای', '?tag=Design'):
            response = self.client.get('/fa/blog/' + query)
            self.assertIsNone(response.context['featured_post'])
            self.assertEqual(response.context['grid_posts'], [self.post])
            self.assertNotContains(response, 'ar-badge')

    def test_unpublished_and_missing_translation_excluded(self):
        self.post.is_published = False
        self.post.save()
        self.assertEqual(self.client.get('/fa/blog/').context['paginator'].count, 0)
        self.post.is_published = True
        self.post.title_en = ''
        self.post.save()
        self.assertEqual(self.client.get('/en/blog/').context['paginator'].count, 0)

    def test_no_js_links_and_actions(self):
        response = self.client.get('/fa/blog/')
        for href in ('/fa/blog/choice/', '/fa/start/', '/fa/assessments/'):
            self.assertContains(response, 'href="' + href + '"')
        self.assertContains(response, 'method="get"')


class ArticleDetailTests(ArticleListTests):
    def test_body_unchanged_toc_and_reserved_cover(self):
        self.post.body_fa = '## عنوان\n\nمتن\n\n### جزئیات\n\n> نقل قول'
        self.post.save()
        response = self.client.get('/fa/blog/choice/')
        self.assertEqual(response.context['article_body'], reader_content(self.post, 'fa')[0])
        self.assertEqual(len(response.context['article_toc']), 2)
        self.assertContains(response, 'ar-hero')
        self.assertContains(response, 'ar-cover-placeholder')
        self.assertContains(response, '<dialog')
        self.assertContains(response, 'aria-controls="article-toc-sheet"')
        self.assertContains(response, 'href="#article-body"')
        self.assertContains(response, '<noscript><div class="ar-mobile-toc">')
        self.assertContains(response, '۲ بخش')

    def test_hero_one_eager_image_explicit_size_and_alt(self):
        self.post.hero_image = 'articles/choice.jpg'
        self.post.save()
        response = self.client.get('/en/blog/choice/')
        self.assertContains(response, 'src="/media/articles/choice.jpg"', count=1)
        self.assertContains(response, 'width="1200" height="630" loading="eager" fetchpriority="high"')
        self.assertContains(response, 'alt="Illustration for Choosing well"')
        self.assertNotContains(response, 'default.jpg')

    def test_no_toc_no_floating_control_and_no_invented_actions(self):
        response = self.client.get('/fa/blog/choice/')
        self.assertEqual(response.context['article_actions'], [])
        self.assertIsNone(response.context['article_service_url'])
        self.assertNotContains(response, '<dialog')
        self.assertNotContains(response, 'data-toc-open')

    def test_actions_only_from_body_ordered_bounded_and_safe(self):
        self.post.body_fa = '\n\n'.join([
            '[تماس](/fa/contact/)', '[خدمت](/fa/services/corporate-website-design/)',
            '[محصول](/fa/crm/)', '[نمونه](/fa/projects/demos/)',
            '[آزمون](/fa/assessments/)', '[خارجی](https://other.example/fa/assessments/)',
            '[نامعتبر](/fa/services/does-not-exist/)', '[زبان دیگر](/en/assessments/)',
            '[تکراری](/fa/assessments/)'])
        self.post.save()
        actions = self.client.get('/fa/blog/choice/').context['article_actions']
        self.assertEqual([x['url'] for x in actions], [
            '/fa/assessments/', '/fa/projects/demos/', '/fa/crm/', '/fa/services/corporate-website-design/'])
        self.assertEqual([x['label'] for x in actions], ['آزمون', 'نمونه', 'محصول', 'خدمت'])

    def test_neighbor_with_only_two_articles(self):
        peer = Post.objects.create(title_fa='مقاله دوم', slug_fa='second', body_fa='متن',
            is_published=True, published_at=timezone.now())
        response = self.client.get('/fa/blog/choice/')
        self.assertEqual(response.context['next_post'], peer)
        self.assertContains(response, '/fa/blog/second/')

    def test_active_templates_and_tags_have_no_retired_asset_references(self):
        roots = (Path(settings.BASE_DIR) / 'blog/templates', Path(settings.BASE_DIR) / 'core/templates',
                 Path(settings.BASE_DIR) / 'blog/templatetags')
        for root in roots:
            for file in root.rglob('*'):
                if file.is_file() and file.suffix in ('.html', '.py'):
                    for retired in ('blog/css/journal.css', 'blog/js/reader.js', 'components/post_card.html'):
                        self.assertNotIn(retired, file.read_text(), str(file))
