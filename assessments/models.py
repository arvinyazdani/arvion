import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse


class Exam(models.Model):
    LANGUAGE_MODES = (("en", "English only"), ("bilingual", "Persian and English"))

    slug = models.SlugField(unique=True)
    title_fa = models.CharField(max_length=180)
    title_en = models.CharField(max_length=180)
    description_fa = models.TextField()
    description_en = models.TextField()
    language_mode = models.CharField(max_length=12, choices=LANGUAGE_MODES)
    question_count = models.PositiveSmallIntegerField(default=50)
    duration_minutes = models.PositiveSmallIntegerField(default=60)
    price_irr = models.PositiveIntegerField(default=500_000)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_order", "id")

    def __str__(self):
        return self.title_en

    def get_absolute_url(self):
        return reverse("assessments:detail", kwargs={"slug": self.slug})


class Order(models.Model):
    STATUSES = (("pending", "Pending"), ("paid", "Paid"), ("failed", "Failed"), ("cancelled", "Cancelled"), ("refunded", "Refunded"))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="assessment_orders")
    exam = models.ForeignKey(Exam, on_delete=models.PROTECT, related_name="orders")
    amount_irr = models.PositiveIntegerField()
    status = models.CharField(max_length=12, choices=STATUSES, default="pending", db_index=True)
    gateway = models.CharField(max_length=30, default="sandbox")
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("user", "exam", "created_at"), name="order_user_exam_created")]

    def __str__(self):
        return f"{self.user_id} / {self.exam_id} / {self.status}"


class PaymentTransaction(models.Model):
    STATUSES = (("initiated", "Initiated"), ("verified", "Verified"), ("failed", "Failed"))

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="transactions")
    gateway = models.CharField(max_length=30)
    external_id = models.CharField(max_length=120, unique=True)
    amount_irr = models.PositiveIntegerField()
    status = models.CharField(max_length=12, choices=STATUSES, default="initiated")
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-created_at",)


class ExamEntitlement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="exam_entitlements")
    exam = models.ForeignKey(Exam, on_delete=models.PROTECT, related_name="entitlements")
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name="entitlement")
    attempts_remaining = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user_id} / {self.exam_id} / {self.attempts_remaining}"
