# core/models/page.py
# مدل صفحات ثابت چندزبانه (About, Terms, ...)
from django.db import models
from parler.models import TranslatableModel, TranslatedFields

class Page(TranslatableModel):
    """
    صفحه‌ی ثابت چندزبانه.
    - slug: شناسه یکتا در URL
    - translations: عنوان و بدنه در هر زبان
    """
    slug = models.SlugField(max_length=80, unique=True)
    translations = TranslatedFields(
        title=models.CharField(max_length=150),
        body=models.TextField(blank=True),
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.safe_translation_getter('title', any_language=True) or self.slug