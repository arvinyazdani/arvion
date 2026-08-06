from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Post


class BlogTests(TestCase):
    def setUp(self):
        self.post = Post.objects.create(
            title_fa="مقاله تست", title_en="Test article", summary_fa="خلاصه", summary_en="Summary",
            body_fa="سلام **دنیا** <script>alert(1)</script>", body_en="Hello **world**",
            slug_fa="مقاله-تست", slug_en="test-article", is_published=True, published_at=timezone.now(),
        )

    def test_list_and_bilingual_detail(self):
        self.assertContains(self.client.get("/fa/blog/"), "مقاله تست")
        response = self.client.get(reverse("blog:detail", args=["test-article"]), {"lang": "en"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test article")

    def test_unpublished_post_is_not_public(self):
        self.post.is_published = False
        self.post.save()
        response = self.client.get(reverse("blog:detail", args=[self.post.slug_fa]), {"lang": "fa"})
        self.assertEqual(response.status_code, 404)

    def test_markdown_html_is_sanitized(self):
        self.assertNotIn("<script>", self.post.body_as_html())
        self.assertIn("<strong>", self.post.body_as_html())
