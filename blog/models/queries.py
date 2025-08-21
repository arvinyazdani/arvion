# blog/models/queries.py
# QuerySet و Managerهای سفارشی برای Post
from django.db import models

class PostQuerySet(models.QuerySet):
    """
    کوئری‌ست سفارشی برای پست‌ها.
    """
    def published(self):
        # مرتب‌سازی بر اساس تاریخ انتشار (جدیدترین اول)
        return self.filter(is_published=True).order_by("-published_at", "-id")
    
    def has_image(self):
        """
        فقط پست‌هایی را نگه می‌دارد که تصویر دارند (نه null و نه خالی).
        """
        return self.exclude(hero_image__isnull=True).exclude(hero_image='')