from django.test import TestCase
from django.utils import timezone, translation
from datetime import timedelta

from blog.models import Post
from blog.presentation import reader_content, reading_minutes


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
        self.assertContains(response, 'href="#article-section-1"')
        self.assertContains(response, '<h2 id="article-section-3">نیاز شما</h2>', html=True)
        self.assertContains(response, '<a href="/fa/contact/">سفارش</a>', html=True)
        self.assertContains(response, "بازگشت به مقاله‌ها")
        self.assertEqual(len(response.context["article_toc"]), 3)
        self.assertContains(self.client.get("/en/blog/guide/"), "In this article")

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
