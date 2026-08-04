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
from projects.models import Project
from services.models import Service
from assessments.models import Exam

class Command(BaseCommand):
    help = "Create initial bilingual demo content for Arvion"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding initial content..."))

        # 1) About Page (FA/EN)
        Page.objects.update_or_create(slug="about", defaults={
            "title_fa": "درباره آروین", "title_en": "About Arvin",
            "body_fa": "من آروین هستم؛ توسعه‌دهندهٔ فول‌استک با تمرکز روی Python/Django.",
            "body_en": "I'm Arvin — a full-stack developer focused on Python/Django.",
        })

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
            Post.objects.update_or_create(slug_en=item["slug_en"], defaults={
                "title_fa": item["fa"]["title"], "title_en": item["en"]["title"],
                "summary_fa": item["fa"]["summary"], "summary_en": item["en"]["summary"],
                "body_fa": item["fa"]["body"], "body_en": item["en"]["body"],
                "slug_fa": item["slug_fa"], "is_published": True, "published_at": timezone.now(),
            })

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
            Project.objects.update_or_create(slug=item["slug_en"], defaults={
                "title_fa": item["fa"]["title"], "title_en": item["en"]["title"],
                "description_fa": item["fa"]["description"], "description_en": item["en"]["description"],
                "repo_url": item["repo"], "demo_url": item["demo"], "is_active": True,
            })

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
            Service.objects.update_or_create(title_en=item["en"]["title"], defaults={
                "title_fa": item["fa"]["title"], "description_fa": item["fa"]["description"],
                "description_en": item["en"]["description"], "price": item["price"], "is_active": True,
            })

        # 5) Assessment products
        Exam.objects.update_or_create(slug="english-placement-a1-c1", defaults={
            "title_fa": "تعیین سطح انگلیسی A1 تا C1",
            "title_en": "English Placement Test A1–C1",
            "description_fa": "ارزیابی مهارت‌های اصلی زبان شامل گرامر، واژگان، درک مطلب و کاربرد زبان.",
            "description_en": "A structured assessment of grammar, vocabulary, reading and use of English.",
            "language_mode": "en", "question_count": 50, "duration_minutes": 55,
            "price_irr": 500_000, "is_active": True, "display_order": 1,
        })
        Exam.objects.update_or_create(slug="python-django-professional", defaults={
            "title_fa": "ارزیابی تخصصی Python و Django",
            "title_en": "Professional Python & Django Assessment",
            "description_fa": "سنجش عملی Python، حل مسئله، دیتابیس، امنیت وب و مهارت‌های لازم برای توسعه پروژه Django.",
            "description_en": "A practical assessment of Python, problem solving, databases, web security and production Django skills.",
            "language_mode": "bilingual", "question_count": 50, "duration_minutes": 70,
            "price_irr": 500_000, "is_active": True, "display_order": 2,
        })

        self.stdout.write(self.style.SUCCESS("✅ Seed done."))
