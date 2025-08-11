# portfolio/models/project.py
from django.db import models
from django.urls import reverse
from parler.models import TranslatableModel, TranslatedFields
from taggit.managers import TaggableManager

class ProjectQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True).order_by("-id")

class Project(TranslatableModel):
    """
    پروژه‌های نمونه کار (چندزبانه)
    """
    translations = TranslatedFields(
        title=models.CharField(max_length=160),
        description=models.TextField(blank=True),
        slug=models.SlugField(max_length=170, allow_unicode=True),
    )
    techs = TaggableManager(blank=True)
    repo_url = models.URLField(blank=True)
    demo_url = models.URLField(blank=True)
    cover_image = models.ImageField(upload_to="projects/", blank=True, null=True)
    is_published = models.BooleanField(default=True)

    objects = ProjectQuerySet.as_manager()

    def __str__(self):
        return self.safe_translation_getter("title", any_language=True) or f"Project {self.pk}"

    def get_absolute_url(self):
        slug = self.safe_translation_getter("slug", any_language=True)
        return reverse("portfolio:detail", args=[slug])