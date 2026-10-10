"""Public article contracts; content and SEO ownership stay with existing models."""
from django.test import TestCase
from django.utils import timezone, translation
from blog.models import Post


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
