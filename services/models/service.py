# services/models/service.py
from django.db import models
from parler.models import TranslatableModel, TranslatedFields

class Service(TranslatableModel):
    """
    سرویس/آموزش چندزبانه با قیمت و وضعیت فعال.
    """
    translations = TranslatedFields(
        title=models.CharField(max_length=160),
        description=models.TextField(blank=True),
    )
    price = models.PositiveIntegerField(default=0)  # تومان یا هر واحد دیگر
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.safe_translation_getter("title", any_language=True) or f"Service {self.pk}"
    