import hashlib
import io
import json
import re
from collections import Counter
from contextlib import redirect_stderr
from html.parser import HTMLParser
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone, translation
from taggit.models import Tag, TaggedItem

from blog.drafts import load_drafts
from blog.models import Post
from core import tests_seo_contract as seo
from core.sitemaps import PostSitemap


BODY_HASHES = {
    "01-cost-of-corporate-website.md": "eacf8eab900e7076d031d484e3267d1c3a0fb41c7c377b22b61a8c5689703393",
    "02-custom-vs-template.md": "c400e5f6f3041102de3674ecadcbe989c9a1f7b80913cc558c2c83f1260daf9e",
    "03-custom-vs-offtheshelf-crm.md": "db453d70246c5c2c03e112b969d963aab994453627c440c522d53f8bba631df1",
    "04-english-teacher-assessment.md": "e297a247b5a692d3b19bf6437e23c5801dda838b6360f1b15c5c9e520cd83a1a",
}


class BodyParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.tags = Counter()
        self.links = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags[tag] += 1
        if tag == "a":
            self.links.append(dict(attrs)["href"])


class ImportBlogDraftTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)

    def run_import(self, *args):
        output = io.StringIO()
        call_command("import_blog_drafts", *args, stdout=output)
        return output.getvalue()

    def test_dry_run_reports_all_four_without_any_writes(self):
        with CaptureQueriesContext(connection) as queries:
            output = self.run_import("--dry-run")
        self.assertEqual(Post.objects.count(), 0)
        self.assertEqual(Tag.objects.count(), 0)
        self.assertEqual(TaggedItem.objects.count(), 0)
        self.assertFalse(any(re.match(r"\s*(INSERT|UPDATE|DELETE)", q["sql"], re.I) for q in queries))
        for draft in load_drafts():
            self.assertIn(draft.slug_fa, output)
        self.assertIn("Created: 4; updated: 0; skipped: 0", output)
        self.assertIn("no database writes", output)

    def test_repeat_import_creates_nothing_and_preserves_rows(self):
        self.run_import()
        before = list(Post.objects.values())
        self.assertIn("Created: 0; updated: 0; skipped: 4", self.run_import())
        self.assertEqual(list(Post.objects.values()), before)
        self.assertEqual(TaggedItem.objects.count(), 8)

    def test_creates_exact_persian_only_unpublished_fields_and_tags(self):
        self.run_import()
        for draft in load_drafts():
            post = Post.objects.get(slug_fa=draft.slug_fa)
            self.assertEqual(post.title_fa, draft.title_fa)
            self.assertEqual(post.summary_fa, draft.summary_fa)
            self.assertEqual(post.body_fa, draft.body_fa)
            self.assertFalse(post.is_published)
            self.assertIsNone(post.published_at)
            for field in ("title_en", "slug_en", "summary_en", "body_en"):
                self.assertIsNone(getattr(post, field))
            self.assertEqual(set(post.tags.names()), set(draft.tags))

    def test_existing_unpublished_is_skipped_without_update(self):
        draft = load_drafts()[0]
        post = Post.objects.create(slug_fa=draft.slug_fa, title_fa="Owner edited title", body_fa="Owner body")
        post.tags.add("Owner tag")
        before = Post.objects.filter(pk=post.pk).values().get()
        self.run_import()
        self.assertEqual(Post.objects.filter(pk=post.pk).values().get(), before)
        self.assertEqual(set(post.tags.names()), {"Owner tag"})

    def test_update_is_explicit_and_preserves_other_editorial_fields(self):
        draft = load_drafts()[0]
        when = timezone.now()
        post = Post.objects.create(slug_fa=draft.slug_fa, title_fa="Edited", title_en="Editorial English",
                                   slug_en="editorial-english", body_en="English body", published_at=when)
        self.assertIn("updated: 1", self.run_import("--update"))
        post.refresh_from_db()
        self.assertEqual(post.title_fa, draft.title_fa)
        self.assertEqual(post.body_fa, draft.body_fa)
        self.assertFalse(post.is_published)
        self.assertEqual(post.published_at, when)
        self.assertEqual(post.title_en, "Editorial English")
        self.assertEqual(post.body_en, "English body")
        self.assertEqual(post.slug_en, "editorial-english")

    def test_published_post_including_future_scheduled_is_never_modified(self):
        for draft in load_drafts()[:2]:
            post = Post.objects.create(slug_fa=draft.slug_fa, title_fa="Owner published title",
                                       body_fa="Published body", is_published=True,
                                       published_at=timezone.now() + timezone.timedelta(days=1))
            post.tags.add("Owner tag")
        before = list(Post.objects.values())
        self.run_import("--update")
        for row in before:
            self.assertEqual(Post.objects.filter(pk=row["id"]).values().get(), row)
            self.assertEqual(set(Post.objects.get(pk=row["id"]).tags.names()), {"Owner tag"})

    def test_update_dry_run_does_not_modify_existing_draft(self):
        draft = load_drafts()[0]
        post = Post.objects.create(slug_fa=draft.slug_fa, title_fa="Owner title")
        before = Post.objects.filter(pk=post.pk).values().get()
        self.assertIn("updated: 1", self.run_import("--dry-run", "--update"))
        self.assertEqual(Post.objects.filter(pk=post.pk).values().get(), before)

    def test_unreviewed_drafts_are_not_public(self):
        self.run_import()
        self.assertEqual(PostSitemap().items(), [])
        for language in ("fa", "en"):
            self.assertEqual(list(self.client.get(f"/{language}/blog/").context["posts"]), [])
            for draft in load_drafts():
                self.assertEqual(self.client.get(f"/{language}/blog/{draft.slug_fa}/").status_code, 404)

    def test_publish_flags_are_rejected_before_any_write(self):
        from blog.management.commands.import_blog_drafts import Command
        for flag in ("--publish", "--published", "--is-published"):
            with self.subTest(flag=flag), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                Command().run_from_argv(["manage.py", "import_blog_drafts", flag])
        self.assertEqual(Post.objects.count(), 0)

    def test_invalid_bundle_fails_before_any_write(self):
        with patch("blog.management.commands.import_blog_drafts.load_drafts", side_effect=ValueError("Invalid bundle")):
            with self.assertRaisesMessage(CommandError, "Invalid bundle"):
                self.run_import()
        self.assertEqual(Post.objects.count(), 0)

    def test_front_matter_cannot_supply_publication_or_english_fields(self):
        draft = load_drafts()[0]
        metadata = {"slug_fa": draft.slug_fa, "title_fa": draft.title_fa,
                    "summary_fa": draft.summary_fa, "tags": list(draft.tags)}
        for key in ("is_published", "published_at", "title_en"):
            with self.subTest(key=key):
                file = Mock(name="draft_file")
                file.name = "invalid.md"
                header = metadata | {key: True}
                file.read_text.return_value = "---\n" + "\n".join(
                    f"{k}: {json.dumps(v)}" for k, v in header.items()) + "\n---\nBody"
                with patch("blog.drafts.DRAFT_DIRECTORY") as directory:
                    directory.glob.return_value = [file]
                    with self.assertRaisesMessage(CommandError, "only slug_fa/title_fa/summary_fa/tags"):
                        self.run_import()
                self.assertEqual(Post.objects.count(), 0)

    def test_tag_failure_rolls_back_entire_bundle(self):
        with patch("taggit.managers._TaggableManager.set", side_effect=RuntimeError("Injected tag failure")):
            with self.assertRaisesMessage(RuntimeError, "Injected tag failure"):
                self.run_import()
        self.assertEqual(Post.objects.count(), 0)
        self.assertEqual(Tag.objects.count(), 0)

    def test_bodies_are_byte_identical_to_source_hashes_and_render_completely(self):
        drafts = load_drafts()
        self.assertEqual({draft.filename for draft in drafts}, set(BODY_HASHES))
        for draft in drafts:
            with self.subTest(file=draft.filename):
                self.assertEqual(hashlib.sha256(draft.body_fa.encode()).hexdigest(), BODY_HASHES[draft.filename])
                html = Post(body_fa=draft.body_fa).body_as_html()
                parsed = BodyParser(html)
                for level in (2, 3):
                    self.assertEqual(parsed.tags[f"h{level}"], len(re.findall(rf"^{'#' * level} ", draft.body_fa, re.M)))
                source_links = re.findall(r"\]\(([^)\s]+)\)", draft.body_fa)
                self.assertEqual(Counter(parsed.links), Counter(source_links))
                self.assertNotIn("&gt;", html)
                self.assertNotRegex(html, r"(?m)^#{1,6} |\[[^\]\n]+\]\(https?://|\*\*|`")
                for forbidden in ("h1", "table", "img"):
                    self.assertEqual(parsed.tags[forbidden], 0)
                if draft.filename.startswith("01-"):
                    self.assertEqual(parsed.tags["blockquote"], 1)
                    self.assertIn("نه پیشنهاد قیمت آرویون", html)

    def test_metadata_lengths_and_internal_routes_are_valid(self):
        from assessments.models import Exam
        # The live English exam is operator-seeded, not a migration fixture.
        Exam.objects.create(slug="english-placement-a1-c1", title_fa="آزمون زبان",
                            title_en="English assessment", description_fa="شرح آزمون",
                            description_en="Exam description", language_mode="en")
        for draft in load_drafts():
            with self.subTest(file=draft.filename):
                self.assertLessEqual(len(draft.title_fa + " | آرویون"), 60)
                self.assertTrue(110 <= len(draft.summary_fa) <= 140)
                for href in BodyParser(Post(body_fa=draft.body_fa).body_as_html()).links:
                    if href.startswith("/"):
                        self.assertEqual(self.client.get(href).status_code, 200, href)


class ImportedDraftSitemapContractTests(seo.WholeSitemapContractTests):
    # Only these test-published Persian articles may omit an English alternate.
    PERSIAN_ONLY_POST_SLUGS = seo.WholeSitemapContractTests.PERSIAN_ONLY_POST_SLUGS | {
        "corporate-website-cost-1405", "custom-website-vs-template",
        "custom-or-ready-made-crm", "english-teacher-assessment",
    }

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command("import_blog_drafts", stdout=io.StringIO())
        # Publication occurs ONLY inside this disposable test fixture.
        Post.objects.filter(slug_fa__in=[draft.slug_fa for draft in load_drafts()]).update(
            is_published=True, published_at=timezone.now())

    def test_imported_articles_publish_in_fa_only_in_test_database(self):
        entries = {(language, post.slug_fa) for language, post in PostSitemap().items()}
        for draft in load_drafts():
            self.assertIn(("fa", draft.slug_fa), entries)
            self.assertNotIn(("en", draft.slug_fa), entries)
            self.assertEqual(self.client.get(f"/en/blog/{draft.slug_fa}/").status_code, 404)
            response = self.client.get(f"/fa/blog/{draft.slug_fa}/")
            head = seo.HeadParser(response.content.decode())
            article = next(node for node in head.json_ld[0]["@graph"] if node["@type"] == "BlogPosting")
            self.assertEqual(article["inLanguage"], "fa")
            self.assertNotIn("author", article)
