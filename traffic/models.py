from django.db import models


class TrafficDay(models.Model):
    date = models.DateField(unique=True)
    page_views = models.PositiveBigIntegerField(default=0)
    unique_visitors = models.PositiveBigIntegerField(default=0)

    class Meta:
        ordering = ("-date",)


class DailyVisitor(models.Model):
    date = models.DateField()
    visitor_hash = models.CharField(max_length=64)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("date", "visitor_hash"), name="unique_daily_visitor")]
        indexes = [models.Index(fields=("date",), name="daily_visitor_date")]


class ActiveVisitor(models.Model):
    visitor_hash = models.CharField(max_length=64, unique=True)
    last_seen = models.DateTimeField(db_index=True)
    path = models.CharField(max_length=160, blank=True)
    is_authenticated = models.BooleanField(default=False)

    class Meta:
        ordering = ("-last_seen",)
