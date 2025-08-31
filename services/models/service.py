# services/models/service.py
from django.db import models

class Service(models.Model):
    """
    مدل سرویس با فیلدهای جداگانه برای زبان فارسی و انگلیسی
    """
    title_fa = models.CharField("عنوان فارسی", max_length=160)
    title_en = models.CharField("عنوان انگلیسی", max_length=160)
    description_fa = models.TextField("توضیحات فارسی", blank=True)
    description_en = models.TextField("توضیحات انگلیسی", blank=True)
    price = models.PositiveIntegerField("قیمت (تومان)", default=0)
    is_active = models.BooleanField("فعال است؟", default=True)

    def __str__(self):
        return self.title_fa