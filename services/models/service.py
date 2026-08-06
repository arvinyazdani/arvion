# services/models/service.py
from django.db import models
from django.urls import reverse

class Service(models.Model):
    """
    مدل سرویس با فیلدهای جداگانه برای زبان فارسی و انگلیسی
    """
    title_fa = models.CharField("عنوان فارسی", max_length=160)
    title_en = models.CharField("عنوان انگلیسی", max_length=160)
    slug = models.SlugField(unique=True)
    short_description_fa = models.CharField("خلاصه فارسی", max_length=240)
    short_description_en = models.CharField("English summary", max_length=240)
    description_fa = models.TextField("توضیحات فارسی", blank=True)
    description_en = models.TextField("توضیحات انگلیسی", blank=True)
    deliverables_fa = models.TextField("خروجی‌ها فارسی", blank=True, help_text="هر مورد در یک خط")
    deliverables_en = models.TextField("English deliverables", blank=True, help_text="One item per line")
    process_fa = models.TextField("فرآیند فارسی", blank=True, help_text="هر مرحله در یک خط")
    process_en = models.TextField("English process", blank=True, help_text="One step per line")
    duration_fa = models.CharField("زمان تقریبی فارسی", max_length=100, blank=True)
    duration_en = models.CharField("English estimated duration", max_length=100, blank=True)
    price = models.PositiveIntegerField("قیمت (تومان)", default=0)
    is_featured = models.BooleanField("خدمت شاخص؟", default=False)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField("فعال است؟", default=True)

    class Meta:
        ordering = ("display_order", "id")

    def __str__(self):
        return self.title_fa

    def get_absolute_url(self):
        return reverse("services:detail", kwargs={"slug": self.slug})

    def deliverables(self, lang):
        value = self.deliverables_fa if lang == "fa" else self.deliverables_en
        return [line.strip() for line in value.splitlines() if line.strip()]

    def process_steps(self, lang):
        value = self.process_fa if lang == "fa" else self.process_en
        return [line.strip() for line in value.splitlines() if line.strip()]
