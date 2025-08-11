# leads/models/lead.py
from django.db import models

class Lead(models.Model):
    """
    درخواست همکاری/آموزش (Lead)
    """
    REQUEST_TYPES = [
        ("project", "Project"),
        ("training", "Training"),
        ("other", "Other"),
    ]
    name = models.CharField(max_length=120)
    email_or_telegram = models.CharField(max_length=120)
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES, default="project")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_reviewed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} — {self.request_type}"