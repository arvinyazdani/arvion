from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    preferred_language = models.CharField(
        max_length=2,
        choices=(("fa", "فارسی"), ("en", "English")),
        default="fa",
    )

    class Meta:
        ordering = ("-date_joined",)

    def __str__(self):
        return self.get_full_name() or self.email
