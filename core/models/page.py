# core/models/page.py
# مدل صفحات ثابت چندزبانه (About, Terms, ...)
from django.db import models
class Page(models.Model):
    """
    صفحه‌ی ثابت چندزبانه.
    - slug: شناسه یکتا در URL
    - translations: عنوان و بدنه در هر زبان
    """
    slug = models.SlugField(max_length=80, unique=True)
    title_fa = models.CharField(max_length=150, default="")
    title_en = models.CharField(max_length=150, default="")
    body_fa = models.TextField(blank=True)
    body_en = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title_fa or self.title_en or self.slug
