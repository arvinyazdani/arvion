# -*- coding: utf-8 -*-
"""
Management command: seed_initial_data
- ایجاد محتوای نمونهٔ دو زبانه (FA/EN) برای صفحه About، پست‌ها، پروژه‌ها و سرویس‌ها.
- برای ترجمه از Parler استفاده می‌شود (set_current_language).
- اجرای دستور:
    python manage.py seed_initial_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

# مدل‌های محتوایی پروژه
from core.models import Page
from blog.models import Post
from portfolio.models import Project
from services.models import Service

class Command(BaseCommand):
    help = "Create initial bilingual demo content for Arvion"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding initial content..."))

        # 1) About Page (FA/EN)
        about, _ = Page.objects.get_or_create(slug="about")
        # فارسی
        about.set_current_language("fa")
        about.title = "درباره آروین"
        about.body = "من آروین هستم؛ توسعه‌دهندهٔ فول‌استک با تمرکز روی Python/Django."
        about.save()
        # انگلیسی
        about.set_current_language("en")
        about.title = "About Arvin"
        about.body = "I'm Arvin — a full‑stack developer focused on Python/Django."
        about.save()

        # 2) Blog Posts (3 نمونه)
        posts_data = [
            {
                "fa": {"title": "شروع Arvion", "summary": "معرفی کوتاه پروژه شخصی.", "body": "سلام دنیا!"},
                "en": {"title": "Starting Arvion", "summary": "A short intro to the personal site.", "body": "Hello world!"},
                "slug_fa": "شروع-arvion",
                "slug_en": "starting-arvion",
            },
            {
                "fa": {"title": "تجربیات Django", "summary": "نکات و ترفندهای جنگو.", "body": "مارک‌داون **فعال** است."},
                "en": {"title": "Django Notes", "summary": "Tips and tricks with Django.", "body": "Markdown **enabled**."},
                "slug_fa": "تجربیات-django",
                "slug_en": "django-notes",
            },
            {
                "fa": {"title": "HTMX در عمل", "summary": "SPA بدون پیچیدگی.", "body": "HTMX عالیه!"},
                "en": {"title": "HTMX in Practice", "summary": "SPA feel without complexity.", "body": "HTMX is great!"},
                "slug_fa": "htmx-در-عمل",
                "slug_en": "htmx-in-practice",
            },
        ]
        for item in posts_data:
            p = Post.objects.create(is_published=True, published_at=timezone.now())
            # FA
            p.set_current_language("fa")
            p.title = item["fa"]["title"]
            p.summary = item["fa"]["summary"]
            p.body = item["fa"]["body"]
            p.slug = item["slug_fa"]
            p.save()
            # EN
            p.set_current_language("en")
            p.title = item["en"]["title"]
            p.summary = item["en"]["summary"]
            p.body = item["en"]["body"]
            p.slug = item["slug_en"]
            p.save()

        # 3) Projects (3 نمونه)
        projects_data = [
            {
                "fa": {"title": "وب‌اپ نمونه ۱", "description": "پروژهٔ فول‌استک با Django."},
                "en": {"title": "Sample WebApp 1", "description": "Full‑stack project with Django."},
                "slug_fa": "وب-اپ-نمونه-۱",
                "slug_en": "sample-webapp-1",
                "repo": "https://github.com/yourname/sample1",
                "demo": "",
            },
            {
                "fa": {"title": "وب‌اپ نمونه ۲", "description": "HTMX و SPA در عمل."},
                "en": {"title": "Sample WebApp 2", "description": "HTMX and SPA in action."},
                "slug_fa": "وب-اپ-نمونه-۲",
                "slug_en": "sample-webapp-2",
                "repo": "https://github.com/yourname/sample2",
                "demo": "",
            },
            {
                "fa": {"title": "ابزارک آموزشی", "description": "آموزش تعاملی Python."},
                "en": {"title": "Learning Widget", "description": "Interactive Python learning."},
                "slug_fa": "ابزارک-آموزشی",
                "slug_en": "learning-widget",
                "repo": "",
                "demo": "",
            },
        ]
        for item in projects_data:
            pr = Project.objects.create(repo_url=item["repo"], demo_url=item["demo"], is_published=True)
            # FA
            pr.set_current_language("fa")
            pr.title = item["fa"]["title"]
            pr.description = item["fa"]["description"]
            pr.slug = item["slug_fa"]
            pr.save()
            # EN
            pr.set_current_language("en")
            pr.title = item["en"]["title"]
            pr.description = item["en"]["description"]
            pr.slug = item["slug_en"]
            pr.save()

        # 4) Services (2 نمونه)
        services_data = [
            {
                "fa": {"title": "آموزش خصوصی Django", "description": "جلسات ۹۰ دقیقه‌ای آنلاین."},
                "en": {"title": "Private Django Training", "description": "90‑minute online sessions."},
                "price": 750000,
            },
            {
                "fa": {"title": "پیاده‌سازی وب‌اپ", "description": "طراحی و ساخت MVP با Django."},
                "en": {"title": "Web App Implementation", "description": "Design & build MVP with Django."},
                "price": 0,
            },
        ]
        for item in services_data:
            s = Service.objects.create(price=item["price"], is_active=True)
            # FA
            s.set_current_language("fa")
            s.title = item["fa"]["title"]
            s.description = item["fa"]["description"]
            s.save()
            # EN
            s.set_current_language("en")
            s.title = item["en"]["title"]
            s.description = item["en"]["description"]
            s.save()

        self.stdout.write(self.style.SUCCESS("✅ Seed done."))