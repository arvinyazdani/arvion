from django.test import TestCase
from django.utils import timezone, translation
from datetime import timedelta

from blog.models import Post
from blog.presentation import reader_content, reading_minutes
from blog.covers import COVER_ALTS, cover_alt


class JournalTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)
        self.post = self.create_post("guide")

    def create_post(self, slug, **changes):
        values = dict(title_fa="راهنمای سایت " + slug, title_en="Website guide " + slug,
                      slug_fa=slug, slug_en=slug, summary_fa="مسیر طراحی و انتخاب سایت",
                      summary_en="Choosing a website", body_fa="## نیاز شما\n\nمتن **راهنما**.\n\n### هزینه\n\n[سفارش](/fa/contact/)\n\n## نیاز شما\n\nپایان.",
                      body_en="## Your needs\n\nGuide.\n\n### Costs\n\nDetails.",
                      is_published=True, published_at=timezone.now())
        values.update(changes)
        return Post.objects.create(**values)

    def test_home_localized_published_only_and_bounded(self):
        for i in range(4):
            self.create_post("extra-" + str(i))
        self.create_post("secret", is_published=False)
        self.create_post("scheduled", published_at=timezone.now() + timedelta(days=1))
        fa_only = self.create_post("fa-only", title_en=None, slug_en=None)
        response = self.client.get("/fa/")
        self.assertEqual(len(response.context["latest_posts"]), 3)
        self.assertContains(response, 'id="home-articles-title"')
        self.assertContains(response, "/fa/blog/fa-only/")
        self.assertNotContains(response, "/fa/blog/secret/")
        response = self.client.get("/en/")
        self.assertEqual(len(response.context["latest_posts"]), 3)
        self.assertNotIn(fa_only, response.context["latest_posts"])
        self.assertNotContains(response, "/en/blog/fa-only/")

    def test_search_topic_paging_and_clear_keep_state(self):
        self.post.tags.add("سایت")
        for i in range(11):
            p = self.create_post("site-" + str(i))
            p.tags.add("سایت")
        response = self.client.get("/fa/blog/", {"q": "راهنمای", "tag": "سایت"})
        self.assertContains(response, "صفحه بعد")
        self.assertContains(response, 'aria-label="پاک‌کردن جستجو"')
        self.assertEqual(response.context["paginator"].count, 12)
        second = self.client.get("/fa/blog/", {"q": "راهنمای", "tag": "سایت", "page": 2})
        self.assertEqual(len(second.context["posts"]), 2)
        self.assertContains(second, "صفحه قبل")
        self.assertContains(second, 'aria-current="true">سایت')
        self.assertNotContains(self.client.get("/en/blog/"), 'aria-current="true">سایت')

    def test_no_result_and_no_cover_have_recovery(self):
        response = self.client.get("/fa/blog/", {"q": "missing-string"})
        self.assertContains(response, "مقاله‌ای پیدا نشد")
        self.assertContains(response, "عبارت کوتاه‌تر")
        self.assertContains(self.client.get("/fa/blog/"), "journal-cover-placeholder")

    def test_detail_stable_toc_preserves_safe_body_and_navigation(self):
        response = self.client.get("/fa/blog/guide/")
        self.assertContains(response, 'href="#section-guide-نیاز-شما"')
        self.assertContains(response, '<h2 id="section-guide-نیاز-شما-2">نیاز شما</h2>', html=True)
        self.assertContains(response, '<a href="/fa/contact/">سفارش</a>', html=True)
        self.assertContains(response, "بازگشت به مقاله‌ها")
        self.assertEqual(len(response.context["article_toc"]), 3)
        self.assertContains(self.client.get("/en/blog/guide/"), "Contents")

    def test_reader_does_not_evaluate_templates_or_restore_unsafe_html(self):
        self.post.body_fa = '## <script>bad()</script>عنوان\n\n{{ request.user }}\n\n[bad](javascript:alert)\n\n```python\nprint("<unsafe>")\n```'
        body, toc = reader_content(self.post, "fa")
        self.assertNotIn("<script>", body)
        self.assertNotIn('href="javascript:', body)
        self.assertIn("{{ request.user }}", body)
        self.assertIn("&lt;unsafe&gt;", body)
        self.assertEqual(len(toc), 1)

    def test_related_excludes_self_draft_future_and_wrong_language(self):
        self.post.tags.add("Web")
        peer = self.create_post("peer")
        peer.tags.add("Web")
        self.create_post("unpublished", is_published=False)
        self.create_post("future", published_at=timezone.now() + timedelta(days=1))
        self.create_post("only-fa", title_en=None, slug_en=None)
        related = self.client.get("/en/blog/guide/").context["related_posts"]
        self.assertEqual(related, [peer])

    def test_estimated_reading_time_nonzero(self):
        self.assertEqual(reading_minutes("", "fa"), 1)
        self.assertEqual(reading_minutes("word " * 401, "en"), 3)

    def test_cover_alts_only_describe_known_v2_assets(self):
        self.assertEqual(len(COVER_ALTS), 8)
        for slug, texts in COVER_ALTS.items():
            self.post.hero_image = 'articles/' + slug + '-v2.jpg'
            self.assertEqual(cover_alt(self.post, 'fa'), texts[0])
            self.assertEqual(cover_alt(self.post, 'en'), texts[1])
        self.post.hero_image = 'articles/corporate-website-cost-1405-v1.jpg'
        self.assertEqual(cover_alt(self.post, 'fa'), 'تصویر توضیحی برای ' + self.post.title_fa)

    def test_parser_preserves_heading_markup_entities_and_link_text(self):
        self.post.body_fa = 'خلاصه & راهنما.\n\n## هزینه **واقعی** & [سفارش](/fa/contact/)\n\nمتن CRM، دقیق.\n\n## هزینه **واقعی** & [سفارش](/fa/contact/)'
        body, toc = reader_content(self.post, "fa")
        self.assertIn('<strong>واقعی</strong>', body)
        self.assertIn('&amp;', body)
        self.assertIn('<a href="/fa/contact/">سفارش</a>', body)
        self.assertIn('<bdi dir="ltr">CRM</bdi>،', body)
        self.assertEqual(toc[0]["title"], 'هزینه واقعی & سفارش')
        self.assertTrue(toc[1]["id"].endswith('-2'))
        self.assertEqual(reader_content(self.post, "fa"), (body, toc))

    def test_external_links_noopener_without_target_and_safe_code(self):
        self.post.body_fa = '[مرجع](https://example.org/?a=1&b=2)\n\n```html\n{% if user %}{{ user }}{% endif %}\n<script>alert(1)</script>\n```'
        body, _ = reader_content(self.post, "fa")
        self.assertIn('rel="noopener"', body)
        self.assertNotIn('target=', body)
        self.assertIn('{% if user %}{{ user }}{% endif %}', body)
        self.assertIn('&lt;script&gt;', body)
        self.assertNotIn('<script>', body)

    def test_latin_phrase_and_contextual_corporate_cta(self):
        self.post.slug_fa = 'corporate-website-cost-1405'
        self.post.body_fa = "متن Let's Encrypt، دقیق.\n\n[فروشگاه](/fa/services/ecommerce-platform/)\n\n[شرکتی](/fa/services/corporate-website-design/)"
        self.post.save()
        response = self.client.get('/fa/blog/corporate-website-cost-1405/')
        self.assertIn('<bdi dir="ltr">Let\'s Encrypt</bdi>،', response.context['article_body'])
        self.assertEqual(response.context['article_service_url'], '/fa/services/corporate-website-design/')

    def test_answer_dek_only_removes_exact_duplicate_not_metadata(self):
        self.post.summary_fa = self.post.title_fa + ' مسیر مناسب را بشناسید.'
        self.post.save()
        response = self.client.get('/fa/blog/guide/')
        self.assertEqual(response.context['article_dek'], 'مسیر مناسب را بشناسید.')
        self.assertContains(response, '<meta name="description" content="' + self.post.summary_fa + '">', html=True)

    def test_featured_list_no_duplicates_one_post_no_empty_panel(self):
        response = self.client.get('/fa/blog/')
        self.assertEqual(response.context['featured_post'], self.post)
        self.assertEqual(response.context['grid_posts'], [])
        self.assertContains(response, 'journal-featured')
        self.assertNotContains(response, 'مقاله‌ای پیدا نشد')
        self.assertEqual(response.content.decode().count('class="journal-card-link"'), 1)

    def test_related_requires_shared_tag_and_neighbors_public_same_language(self):
        self.post.tags.add('Web')
        matching = self.create_post('matching')
        matching.tags.add('Web')
        self.create_post('not-related')
        self.create_post('fa-only', title_en=None, slug_en=None)
        self.create_post('draft', is_published=False)
        response = self.client.get('/en/blog/guide/')
        self.assertEqual(response.context['related_posts'], [matching])
        self.assertNotContains(response, '/en/blog/draft/')
        self.assertNotContains(response, '/en/blog/fa-only/')
        self.assertIsNotNone(response.context['next_post'])

    def test_cover_loading_progress_copy_and_toc_mobile_default(self):
        self.post.hero_image = 'articles/test.jpg'
        self.post.save()
        response = self.client.get('/fa/blog/guide/')
        self.assertContains(response, 'loading="eager"')
        self.assertContains(response, 'fetchpriority="high"')
        self.assertContains(response, 'height="630"')
        self.assertContains(response, '<details class="journal-toc">')
        self.assertContains(response, 'data-copy-article')
        self.assertContains(response, 'role="progressbar"')
        self.assertNotContains(response, 'article:modified_time')
