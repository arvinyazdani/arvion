import uuid

from django.db import models


class DemoTemplate(models.Model):
    CATEGORY_CHOICES = (
        ("ecommerce", "فروشگاه اینترنتی"), ("restaurant", "رستوران و کافه"),
        ("portfolio", "پورتفولیو"), ("corporate", "وب‌سایت شرکتی"),
        ("clinic", "کلینیک"), ("education", "آموزش"),
    )

    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, db_index=True)
    title_fa = models.CharField(max_length=120)
    title_en = models.CharField(max_length=120)
    tagline_fa = models.CharField(max_length=220)
    tagline_en = models.CharField(max_length=220)
    fictional_brand_fa = models.CharField(max_length=120)
    fictional_brand_en = models.CharField(max_length=120)
    style_key = models.CharField(max_length=30)
    default_features = models.JSONField(default=list, blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("category", "display_order", "pk")

    def __str__(self):
        return self.title_fa


class DemoSelection(models.Model):
    """Anonymous, session-bound design choices until the visitor submits an enquiry."""
    public_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    template = models.ForeignKey(DemoTemplate, on_delete=models.PROTECT, related_name="selections")
    session_key = models.CharField(max_length=64, db_index=True)
    selections = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
