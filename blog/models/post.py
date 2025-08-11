# blog/models/post.py
# مدل چندزبانه‌ی پست بلاگ
from django.db import models
from django.urls import reverse
from parler.models import TranslatableModel, TranslatedFields
from taggit.managers import TaggableManager
import markdown
from .queries import PostQuerySet

class Post(TranslatableModel):
    """
    پست بلاگ (چندزبانه)
    - translations: title/summary/body/slug per language
    - hero_image: تصویر کاور
    - is_published/published_at: انتشار
    """
    translations = TranslatedFields(
        title=models.CharField(max_length=160),
        summary=models.CharField(max_length=240, blank=True),
        body=models.TextField(),
        slug=models.SlugField(max_length=170, allow_unicode=True),
    )
    hero_image = models.ImageField(upload_to="blog/", blank=True, null=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    tags = TaggableManager(blank=True)

    # اتصال QuerySet سفارشی
    objects = PostQuerySet.as_manager()

    class Meta:
        # نکته: یکتایی slug را در سطح ترجمه‌ها مدیریت می‌کنیم (از طریق ادمین/اعتبارسنجی).
        verbose_name = "Post"
        verbose_name_plural = "Posts"

    def __str__(self):
        return self.safe_translation_getter("title", any_language=True) or f"Post {self.pk}"

    def get_absolute_url(self):
        """
        URL بر اساس slug زبان جاری. برای i18n خوبه slug per-language باشد.
        """
        slug = self.safe_translation_getter("slug", any_language=True)
        return reverse("blog:detail", args=[slug])

    def body_as_html(self):
        """
        رندر مارک‌داون بدنه پست برای نمایش در قالب.
        """
        source = self.safe_translation_getter("body", any_language=True) or ""
        return markdown.markdown(source, extensions=["fenced_code"])