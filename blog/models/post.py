# blog/models/post.py
# مدل چندزبانه‌ی پست بلاگ
from django.db import models
from django.urls import reverse
from taggit.managers import TaggableManager
import markdown
from .queries import PostQuerySet
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

def validate_image_size(image):
    max_size = 1 * 1024 * 1024  # 1 MB
    if image.size > max_size:
        raise ValidationError("حجم تصویر نباید بیشتر از ۱ مگابایت باشد.")

class Post(models.Model):
    """
    پست بلاگ (چندزبانه)
    - translations: title/summary/body/slug per language
    - hero_image: تصویر کاور
    - is_published/published_at: انتشار
    """
    title_fa = models.CharField("عنوان (فارسی)", max_length=160, blank=True, null=True)
    title_en = models.CharField("Title (English)", max_length=160, blank=True, null=True)
    summary_fa = models.CharField("خلاصه (فارسی)", max_length=240, blank=True, null=True)
    summary_en = models.CharField("Summary (English)", max_length=240, blank=True, null=True)
    body_fa = models.TextField("متن کامل (فارسی)", blank=True, null=True)
    body_en = models.TextField("Full Body (English)", blank=True, null=True)
    slug_fa = models.SlugField("نامک (فارسی)", max_length=170, allow_unicode=True, blank=True, null=True)
    slug_en = models.SlugField("Slug (English)", max_length=170, allow_unicode=True, blank=True, null=True)
    hero_image = models.ImageField(
        upload_to="articles/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"]),
            validate_image_size,
        ]
    )
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
        # Fallback to Persian title if available
        return self.title_fa or f"Post {self.pk}"

    def get_absolute_url(self):
        """
        URL بر اساس slug زبان جاری. برای i18n خوبه slug per-language باشد.
        توجه: مسیریابی زبان‌محور باید در جای دیگری مدیریت شود.
        """
        # Fallback to Persian slug
        slug = self.slug_fa
        return reverse("blog:detail", args=[slug])

    def body_as_html(self):
        """
        رندر مارک‌داون بدنه پست برای نمایش در قالب.
        """
        # Fallback to Persian body
        source = self.body_fa or ""
        return markdown.markdown(source, extensions=["fenced_code"])