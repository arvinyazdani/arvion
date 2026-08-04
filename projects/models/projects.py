from django.db import models
from django.urls import reverse
from taggit.managers import TaggableManager

class Project(models.Model):
    title_fa = models.CharField("عنوان فارسی", max_length=200, help_text="عنوان پروژه به فارسی")
    title_en = models.CharField("عنوان انگلیسی", max_length=200, help_text="Project title in English")

    description_fa = models.TextField("توضیح فارسی", blank=True, help_text="توضیحات تکمیلی به فارسی")
    description_en = models.TextField("توضیح انگلیسی", blank=True, help_text="Detailed description in English")

    image = models.ImageField("تصویر", upload_to="projects/images/", blank=True, null=True)
    demo_url = models.URLField("لینک دمو", blank=True)
    repo_url = models.URLField("مخزن کد", blank=True)
    technologies = TaggableManager("تکنولوژی‌ها", blank=True)

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

    def get_absolute_url(self):
        return reverse("projects:detail", kwargs={"slug": self.slug})
