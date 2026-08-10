from django.core.exceptions import ValidationError
from django.db import models


class CompanyProfile(models.Model):
    legal_name_fa = models.CharField(max_length=180)
    legal_name_en = models.CharField(max_length=180)
    company_type_fa = models.CharField(max_length=80, default="با مسئولیت محدود")
    brand_name = models.CharField(max_length=80, default="Rvion")
    registration_number = models.CharField(max_length=30)
    national_id = models.CharField(max_length=30)
    established_date_fa = models.CharField(max_length=20)
    chief_executive_fa = models.CharField(max_length=120)
    chief_executive_en = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    postal_code = models.CharField(max_length=20)
    address_fa = models.TextField()
    address_en = models.TextField()
    domain = models.CharField(max_length=120, default="rvionai.com")
    support_hours_fa = models.CharField(max_length=180)
    support_hours_en = models.CharField(max_length=180)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company profile"
        verbose_name_plural = "Company profile"

    def clean(self):
        if not self.pk and CompanyProfile.objects.exists():
            raise ValidationError("Only one company profile can exist.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.legal_name_fa
