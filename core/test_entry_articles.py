import base64
import gzip
import json
from django.test import TestCase, override_settings
from django.utils import timezone, translation
from blog.models import Post
from core.templatetags.entry_ui import entry_payload
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser


@override_settings(RVION_ENTRY_ENABLED=True)
class EntryArticleTests(TestCase):
    def setUp(self):
        translation.activate('fa')
        self.addCleanup(translation.deactivate_all)

    def scene(self, response):
        html = response.content.decode()
        payload = json.loads(html.split('id="rvion-entry-payload" type="application/json">')[1].split('</script>')[0])
        return gzip.decompress(base64.b64decode(payload['scene_gzip'])).decode()

    def test_three_latest_current_language_and_real_hrefs(self):
        for i in range(5):
            Post.objects.create(title_fa='مقاله ' + str(i), slug_fa='article-' + str(i),
                title_en='Guide ' + str(i) if i < 4 else None,
                slug_en='guide-' + str(i) if i < 4 else None,
                body_fa='متن', body_en='Text', is_published=True, published_at=timezone.now())
        Post.objects.create(title_fa='محرمانه', slug_fa='unpublished', is_published=False)
        for lang in ('fa', 'en'):
            response = self.client.get('/' + lang + '/')
            scene = self.scene(response)
            self.assertEqual(scene.count('class="ar-gate-item"'), 3)
            self.assertIn('href="/' + lang + '/blog/"', scene)
            for post in response.context['latest_posts']:
                self.assertIn('href="/' + lang + '/blog/' + getattr(post, 'slug_' + lang) + '/"', scene)
            self.assertNotIn('unpublished', scene)
            if lang == 'en':
                self.assertNotRegex(scene, r'[\u0600-\u06ff]')
            self.assertIn('data-entry-id="enter"', scene)

    def test_no_articles_omits_section(self):
        response = self.client.get('/fa/')
        self.assertNotIn('ar-gate', self.scene(response))

    def test_render_payload_reuses_prefetched_data_without_queries(self):
        post = Post.objects.create(title_fa='نمونه', slug_fa='sample', body_fa='متن',
            is_published=True, published_at=timezone.now())
        post.tags.add('سایت')
        posts = list(Post.objects.prefetch_related('tags'))
        request = RequestFactory().get('/fa/')
        request.user = AnonymousUser()
        with self.assertNumQueries(0):
            output = entry_payload({'request': request, 'lang': 'fa', 'latest_posts': posts})
        self.assertIn('scene_gzip', output)

    @override_settings(RVION_ENTRY_ENABLED=False)
    def test_disabled_gate_has_readable_no_js_home_article_links(self):
        Post.objects.create(title_fa='نمونه', slug_fa='sample', body_fa='متن',
            is_published=True, published_at=timezone.now())
        response = self.client.get('/fa/')
        self.assertNotContains(response, 'id="rvion-entry-payload"')
        self.assertContains(response, 'href="/fa/blog/sample/"')
