from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.urls import reverse
from django.utils import translation

from blog.languages import available_post_languages
from blog.models import Post
from projects.models import DemoTemplate

from .indexnow import submit_urls


def _post_urls(post):
    urls = []
    for language in available_post_languages(post):
        slug = getattr(post, f"slug_{language}")
        with translation.override(language):
            urls.append(f"{settings.SITE_URL.rstrip('/')}{reverse('blog:detail', args=[slug])}")
    return urls


def _demo_urls(demo):
    urls = []
    for language in ("fa", "en"):
        with translation.override(language):
            urls.append(f"{settings.SITE_URL.rstrip('/')}{reverse('projects:demo_preview', args=[demo.slug])}")
    return urls


@receiver(pre_save, sender=Post)
def post_indexnow_change_marker(sender, instance, raw=False, **kwargs):
    if raw:
        instance._indexnow_changed = False
        return
    if not getattr(settings, "INDEXNOW_ENABLED", False) or not instance.pk:
        instance._indexnow_changed = True
        return
    old = sender.objects.filter(pk=instance.pk).values(
        "title_fa", "title_en", "summary_fa", "summary_en", "body_fa", "body_en",
        "slug_fa", "slug_en", "is_published", "published_at", "hero_image",
    ).first()
    fields = ("title_fa", "title_en", "summary_fa", "summary_en", "body_fa", "body_en",
              "slug_fa", "slug_en", "is_published", "published_at", "hero_image")
    instance._indexnow_was_public = bool(old and old["is_published"] and old["published_at"] and old["published_at"] <= timezone.now())
    instance._indexnow_changed = not old or any(old[field] != getattr(instance, field) for field in fields)


@receiver(post_save, sender=Post)
def notify_indexnow_for_post(sender, instance, raw=False, **kwargs):
    if raw:
        return
    if not getattr(settings, "INDEXNOW_ENABLED", False) or not getattr(instance, "_indexnow_changed", True):
        return
    is_public = instance.is_published and instance.published_at and instance.published_at <= timezone.now()
    if is_public or getattr(instance, "_indexnow_was_public", False):
        urls = _post_urls(instance)
        transaction.on_commit(lambda: submit_urls(urls))


@receiver(pre_save, sender=DemoTemplate)
def demo_indexnow_change_marker(sender, instance, raw=False, **kwargs):
    if raw:
        instance._indexnow_changed = False
        return
    if not getattr(settings, "INDEXNOW_ENABLED", False) or not instance.pk:
        instance._indexnow_changed = True
        return
    old = sender.objects.filter(pk=instance.pk).values(
        "category", "title_fa", "title_en", "tagline_fa", "tagline_en", "style_key",
        "default_features", "display_order", "is_active",
    ).first()
    instance._indexnow_was_public = bool(old and old["is_active"])
    instance._indexnow_changed = not old or any(
        old[field] != getattr(instance, field) for field in (
            "category", "title_fa", "title_en", "tagline_fa", "tagline_en", "style_key",
            "default_features", "display_order", "is_active")
    )


@receiver(post_save, sender=DemoTemplate)
def notify_indexnow_for_demo(sender, instance, raw=False, **kwargs):
    if raw or not getattr(settings, "INDEXNOW_ENABLED", False) or not getattr(instance, "_indexnow_changed", True):
        return
    if not instance.is_active and not getattr(instance, "_indexnow_was_public", False):
        return
    urls = _demo_urls(instance)
    transaction.on_commit(lambda: submit_urls(urls))
