from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone, translation

from blog.covers import COVER_ALTS
from blog.models import Post
from blog.presentation import article_topics


class ArticleOpenerCoverTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        setting = override_settings(MEDIA_ROOT=self.media.name)
        setting.enable()
        self.addCleanup(setting.disable)
        self.post = Post.objects.create(slug_fa="corporate-website-cost-1405", title_fa="راهنمای سایت",
            slug_en="website-guide", title_en="Website guide", summary_fa="خلاصه", summary_en="Summary",
            body_fa="## هدف\n\nنخستین جمله واقعی است. جمله بعدی است.\n\n### جزئیات\n\nتوضیحات.\n\n## مسیر\n\n" + "واژه " * 30,
            body_en="## Goal\n\nThe first sentence is real. The second is longer.\n\n### Details\n\nDetails.\n\n## Path\n\nChoose a useful next step.",
            is_published=True, published_at=timezone.now())

    def test_real_h2_topics_first_sentence_and_controls_in_initial_html(self):
        for lang, label in (("fa", "در این مقاله"), ("en", "In this article")):
            response = self.client.get("/" + lang + "/blog/" + getattr(self.post, "slug_" + lang) + "/")
            topics = response.context["article_topics"]
            self.assertEqual(len(topics), 2)
            self.assertEqual(topics[0]["description"], "نخستین جمله واقعی است." if lang == "fa" else "The first sentence is real.")
            for topic in topics:
                self.assertLessEqual(len(topic["description"]), 90)
                self.assertContains(response, 'href="#' + topic["id"] + '"')
            self.assertContains(response, label)
            self.assertContains(response, "data-opener-skip")
            self.assertContains(response, "data-opener-replay")
            self.assertContains(response, 'class="ar-opener-route"')

    def test_list_intro_reads_only_the_first_item(self):
        topics = article_topics('<h2 id="first">Goal</h2><ul><li>First choice</li><li>Second choice</li></ul>',
                                [{"id": "first", "title": "Goal", "level": "2"}])
        self.assertEqual(topics[0]["description"], "First choice")

    def test_dry_run_never_writes_database_or_media(self):
        output = StringIO()
        before = Post.objects.values().get(pk=self.post.pk)
        call_command("attach_article_covers", dry_run=True, stdout=output)
        self.assertEqual(before, Post.objects.values().get(pk=self.post.pk))
        self.assertEqual(list(Path(self.media.name).rglob("*.jpg")), [])
        self.assertIn("Would attach: 1; skipped: 7", output.getvalue())

    def test_mapping_all_eight_and_repeated_execution_is_noop(self):
        for slug in COVER_ALTS:
            Post.objects.get_or_create(slug_fa=slug, defaults={"title_fa": slug})
        before = {p.pk: (p.body_fa, p.is_published, p.published_at) for p in Post.objects.all()}
        output = StringIO()
        call_command("attach_article_covers", stdout=output)
        self.assertIn("Attached: 8; skipped: 0", output.getvalue())
        images = list(Path(self.media.name).rglob("*.jpg"))
        self.assertEqual(len(images), 8)
        names = dict(Post.objects.values_list("pk", "hero_image"))
        call_command("attach_article_covers", stdout=StringIO())
        self.assertEqual(names, dict(Post.objects.values_list("pk", "hero_image")))
        self.assertEqual(len(list(Path(self.media.name).rglob("*.jpg"))), 8)
        self.assertEqual(before, {p.pk: (p.body_fa, p.is_published, p.published_at) for p in Post.objects.all()})

    def test_existing_cover_never_replaced(self):
        self.post.hero_image = "articles/owner-cover.webp"
        self.post.save(update_fields=["hero_image"])
        call_command("attach_article_covers", stdout=StringIO())
        self.post.refresh_from_db()
        self.assertEqual(self.post.hero_image.name, "articles/owner-cover.webp")
        self.assertEqual(list(Path(self.media.name).rglob("*.jpg")), [])

    def test_cover_hero_social_image_and_lazy_decorative_cards(self):
        call_command("attach_article_covers", stdout=StringIO())
        self.post.refresh_from_db()
        response = self.client.get("/fa/blog/" + self.post.slug_fa + "/")
        self.assertContains(response, 'loading="eager" fetchpriority="high"')
        self.assertContains(response, 'property="og:image" content="https://rvionai.com' + self.post.hero_image.url + '"')
        self.assertContains(response, 'property="og:image:type" content="image/jpeg"')
        listing = self.client.get("/fa/blog/")
        self.assertContains(listing, 'alt="" width="1200" height="630" loading="lazy"')
        self.assertNotContains(listing, 'fetchpriority="high"')
