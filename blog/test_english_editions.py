import hashlib
import re
import json
import os
import runpy
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone, translation
from django.urls import resolve

from blog.drafts import load_drafts
from blog.english_editions import ENGLISH_FIELDS, load_english_editions, publish_english_editions
from blog.models import Post
from core.sitemaps import PostSitemap
from core.tests_seo_contract import HeadParser


class EnglishEditionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editions = load_english_editions()
        for draft in load_drafts():
            post = Post.objects.create(
                slug_fa=draft.slug_fa, title_fa=draft.title_fa,
                summary_fa=draft.summary_fa, body_fa=draft.body_fa,
                is_published=True, published_at=timezone.now(),
                hero_image="articles/original.jpg",
            )
            post.tags.set(draft.tags)

    def setUp(self):
        translation.activate("en")
        self.addCleanup(translation.deactivate_all)

    def preserved(self):
        return [(post.pk, post.slug_fa, post.title_fa, post.summary_fa,
                 hashlib.sha256(post.body_fa.encode()).hexdigest(), post.hero_image.name,
                 post.is_published, post.published_at, tuple(post.tags.names()))
                for post in Post.objects.order_by("pk")]

    def test_eight_complete_unique_english_editions(self):
        self.assertEqual(len(self.editions), 8)
        for item in self.editions:
            self.assertNotIn("/fa/", item["body_en"])
            self.assertNotIn("تومان", item["body_en"])
            post = Post(body_en=item["body_en"])
            html = post.body_as_html_en()
            self.assertIn("<h2>", html)
            self.assertNotIn("<script", html)
            self.assertNotIn("<h1", html)
            for href in re.findall(r'href="(/en/[^"#]*)', html):
                resolve(href)

    def test_default_and_explicit_dry_runs_write_nothing(self):
        for args in ([], ["--dry-run"]):
            with self.subTest(args=args):
                output = StringIO()
                call_command("publish_english_articles", *args, stdout=output)
                self.assertIn("DRY RUN, no writes: 8 updated", output.getvalue())
                self.assertEqual(Post.objects.exclude(body_en__isnull=True).count(), 0)

    def test_apply_is_idempotent_and_preserves_source_and_shared_fields(self):
        before = self.preserved()
        self.assertEqual(publish_english_editions(apply=True)["updated"], 8)
        with patch.object(Post, "save", side_effect=AssertionError("Unexpected write")):
            self.assertEqual(publish_english_editions(apply=True)["unchanged"], 8)
        self.assertEqual(self.preserved(), before)

    def test_missing_or_unpublished_source_fails_without_partial_updates(self):
        for state in ("unpublished", "future", "missing"):
            with self.subTest(state=state), self.atomic_subtest():
                post = Post.objects.get(slug_fa=self.editions[-1]["slug_fa"])
                if state == "missing":
                    post.delete()
                elif state == "future":
                    post.published_at = timezone.now() + timezone.timedelta(days=1)
                    post.save()
                else:
                    post.is_published = False
                    post.save()
                with self.assertRaises(ValueError):
                    publish_english_editions(apply=True)
                self.assertEqual(Post.objects.exclude(body_en__isnull=True).count(), 0)

    @staticmethod
    def atomic_subtest():
        from contextlib import contextmanager
        from django.db import transaction

        @contextmanager
        def isolated():
            with transaction.atomic():
                yield
                transaction.set_rollback(True)
        return isolated()

    def test_slug_collision_or_url_change_is_rejected(self):
        first = self.editions[0]
        other = Post.objects.create(slug_en=first["slug_en"], title_en="Unrelated")
        with self.assertRaises(ValueError):
            publish_english_editions(apply=True)
        other.delete()
        post = Post.objects.get(slug_fa=first["slug_fa"])
        post.slug_en = "already-public-url"
        post.save()
        with self.assertRaises(ValueError):
            publish_english_editions(apply=True)
        self.assertEqual(Post.objects.exclude(body_en__isnull=True).count(), 0)

    def test_database_error_rolls_back_every_english_change(self):
        real_save = Post.save
        calls = []

        def fail_second(post, *args, **kwargs):
            calls.append(post.pk)
            if len(calls) == 2:
                raise RuntimeError("Injected failure")
            return real_save(post, *args, **kwargs)

        with patch.object(Post, "save", fail_second), self.assertRaises(RuntimeError):
            publish_english_editions(apply=True)
        self.assertEqual(Post.objects.exclude(body_en__isnull=True).count(), 0)

    def test_public_urls_metadata_sitemap_and_language_switch(self):
        publish_english_editions(apply=True)
        response = self.client.get("/en/blog/")
        self.assertEqual(response.status_code, 200)
        titles, descriptions = set(), set()
        for item in self.editions:
            url = f"/en/blog/{item['slug_en']}/"
            page = self.client.get(url)
            self.assertEqual(page.status_code, 200)
            self.assertContains(page, item["title_en"])
            self.assertEqual(page.context["language_switch_url"], f"/fa/blog/{item['slug_fa']}/")
            head = HeadParser(page.content.decode())
            self.assertLessEqual(len(head.title.strip()), 60)
            self.assertTrue(90 <= len(head.meta["description"]) <= 155)
            self.assertEqual(head.h1_count, 1)
            self.assertNotIn(head.title, titles)
            self.assertNotIn(head.meta["description"], descriptions)
            titles.add(head.title)
            descriptions.add(head.meta["description"])
            self.assertEqual(set(page.context["alternate_urls"]), {"fa", "en"})
            self.assertIn({"rel": "canonical", "href": "https://rvionai.com" + url}, head.links)
            self.assertContains(page, 'dir="ltr"')
        self.assertEqual(len([x for x in PostSitemap().items() if x[0] == "en"]), 8)

    def test_code_example_renders_literally_and_all_thirty_questions_exist(self):
        item = self.editions[-1]
        html = Post(body_en=item["body_en"]).body_as_html_en()
        self.assertIn("<pre><code", html)
        self.assertIn('{% extends &quot;base.html&quot; %}', html)
        self.assertIn("{{ block.super }}", html)
        for number in range(1, 31):
            self.assertIn(f"<h3>{number}.", html)

    def run_release_script(self, **environment):
        root = Path(__file__).resolve().parents[1]
        env = {"RVION_ENGLISH_RELEASE_DIRECTORY": str(root / "blog"),
               "RVION_ENGLISH_APPLY": "0", **environment}
        output = StringIO()
        with patch.dict(os.environ, env), redirect_stdout(output):
            runpy.run_path(str(root / "ops/publish_english_content.py"))
        return output.getvalue()

    def test_release_script_dry_run_has_no_side_effects(self):
        before = self.preserved()
        self.assertIn("no database or backup writes", self.run_release_script())
        self.assertEqual(before, self.preserved())
        self.assertEqual(Post.objects.exclude(body_en__isnull=True).count(), 0)

    def test_release_script_validates_backup_and_preserves_every_other_field(self):
        before = self.preserved()
        with TemporaryDirectory() as directory:
            backup = Path(directory) / "snapshot"
            output = self.run_release_script(RVION_ENGLISH_APPLY="1",
                                             RVION_ENGLISH_BACKUP_DIRECTORY=str(backup))
            rows = json.loads((backup / "before.json").read_text())
            self.assertEqual(len(rows), 8)
            self.assertTrue(all(row["body_en"] is None for row in rows))
            self.assertEqual((backup / "before.json").stat().st_mode & 0o777, 0o600)
            self.assertIn("Non-English fields unchanged", output)
        self.assertEqual(before, self.preserved())

    def test_release_backup_failure_prevents_publication(self):
        with TemporaryDirectory() as directory:
            with self.assertRaises(FileExistsError):
                self.run_release_script(RVION_ENGLISH_APPLY="1",
                                        RVION_ENGLISH_BACKUP_DIRECTORY=directory)
        self.assertEqual(Post.objects.exclude(body_en__isnull=True).count(), 0)
