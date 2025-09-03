from django.db import models

class Project(models.Model):
    title_fa = models.CharField("عنوان فارسی", max_length=200, help_text="عنوان پروژه به فارسی")
    title_en = models.CharField("عنوان انگلیسی", max_length=200, help_text="Project title in English")

    description_fa = models.TextField("توضیح فارسی", blank=True, help_text="توضیحات تکمیلی به فارسی")
    description_en = models.TextField("توضیح انگلیسی", blank=True, help_text="Detailed description in English")

    image = models.ImageField("تصویر", upload_to="projects/images/")
    link = models.URLField("لینک پروژه", blank=True)

    slug = models.SlugField("اسلاگ", unique=True)
    is_active = models.BooleanField("فعال؟", default=True)

    created_at = models.DateTimeField("زمان ساخت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    class Meta:
        verbose_name = "پروژه"
        verbose_name_plural = "پروژه‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title_fa or self.title_en or "پروژه بدون عنوان"