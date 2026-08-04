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


class Skill(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="skills")
    code = models.SlugField(max_length=60)
    title_fa = models.CharField(max_length=120)
    title_en = models.CharField(max_length=120)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("display_order", "id")
        constraints = [models.UniqueConstraint(fields=("exam", "code"), name="unique_exam_skill_code")]

    def __str__(self):
        return f"{self.exam.slug} / {self.code}"


class ExamVersion(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.PROTECT, related_name="versions")
    version = models.PositiveSmallIntegerField()
    is_published = models.BooleanField(default=False, db_index=True)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-version",)
        constraints = [models.UniqueConstraint(fields=("exam", "version"), name="unique_exam_version")]

    def __str__(self):
        return f"{self.exam.slug} v{self.version}"


class ExamSection(models.Model):
    version = models.ForeignKey(ExamVersion, on_delete=models.CASCADE, related_name="sections")
    code = models.SlugField(max_length=60)
    title_fa = models.CharField(max_length=140)
    title_en = models.CharField(max_length=140)
    question_count = models.PositiveSmallIntegerField()
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("display_order", "id")
        constraints = [models.UniqueConstraint(fields=("version", "code"), name="unique_version_section_code")]

    def __str__(self):
        return f"{self.version} / {self.code}"


class Question(models.Model):
    DIFFICULTIES = ((1, "Foundation"), (2, "Easy"), (3, "Intermediate"), (4, "Advanced"), (5, "Expert"))

    version = models.ForeignKey(ExamVersion, on_delete=models.PROTECT, related_name="questions")
    section = models.ForeignKey(ExamSection, on_delete=models.PROTECT, related_name="questions")
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT, related_name="questions")
    prompt_fa = models.TextField()
    prompt_en = models.TextField()
    difficulty = models.PositiveSmallIntegerField(choices=DIFFICULTIES, default=3)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    explanation_fa = models.TextField(blank=True)
    explanation_en = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("id",)
        indexes = [models.Index(fields=("version", "section", "is_active"), name="question_pool_lookup")]

    def __str__(self):
        return self.prompt_en[:80]


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text_fa = models.TextField()
    text_en = models.TextField()
    is_correct = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("display_order", "id")

    def __str__(self):
        return self.text_en[:80]


class Attempt(models.Model):
    STATUSES = (
        ("ready", "Ready"), ("in_progress", "In progress"), ("submitted", "Submitted"),
        ("expired", "Expired"), ("scoring", "Scoring"), ("completed", "Completed"),
        ("invalidated", "Invalidated"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="exam_attempts")
    exam = models.ForeignKey(Exam, on_delete=models.PROTECT, related_name="attempts")
    version = models.ForeignKey(ExamVersion, on_delete=models.PROTECT, related_name="attempts")
    entitlement = models.OneToOneField(ExamEntitlement, on_delete=models.PROTECT, related_name="attempt")
    status = models.CharField(max_length=14, choices=STATUSES, default="ready", db_index=True)
    started_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    current_position = models.PositiveSmallIntegerField(default=1)
    integrity_score = models.PositiveSmallIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("user", "status", "created_at"), name="attempt_user_status")]

    def __str__(self):
        return f"{self.user_id} / {self.exam_id} / {self.status}"

    def get_absolute_url(self):
        return reverse("assessments:attempt", kwargs={"pk": self.pk})


class AttemptQuestion(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="attempt_questions")
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name="attempt_uses")
    position = models.PositiveSmallIntegerField()
    choice_order = models.JSONField(default=list)
    selected_choice = models.ForeignKey(Choice, on_delete=models.PROTECT, blank=True, null=True, related_name="selected_in_attempts")
    answered_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("position",)
        constraints = [
            models.UniqueConstraint(fields=("attempt", "position"), name="unique_attempt_position"),
            models.UniqueConstraint(fields=("attempt", "question"), name="unique_attempt_question"),
        ]


class IntegrityEvent(models.Model):
    EVENT_TYPES = (("tab_hidden", "Tab hidden"), ("window_blur", "Window blur"), ("copy", "Copy"), ("paste", "Paste"), ("other", "Other"))

    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="integrity_events")
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)


class AttemptResult(models.Model):
    attempt = models.OneToOneField(Attempt, on_delete=models.PROTECT, related_name="result")
    correct_count = models.PositiveSmallIntegerField(default=0)
    incorrect_count = models.PositiveSmallIntegerField(default=0)
    unanswered_count = models.PositiveSmallIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    level_code = models.CharField(max_length=30)
    level_title_fa = models.CharField(max_length=120)
    level_title_en = models.CharField(max_length=120)
    summary_fa = models.TextField()
    summary_en = models.TextField()
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-generated_at",)

    def __str__(self):
        return f"{self.attempt_id} / {self.percentage}%"


class SkillResult(models.Model):
    result = models.ForeignKey(AttemptResult, on_delete=models.CASCADE, related_name="skill_results")
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT, related_name="results")
    correct_count = models.PositiveSmallIntegerField(default=0)
    question_count = models.PositiveSmallIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        ordering = ("skill__display_order", "skill_id")
        constraints = [models.UniqueConstraint(fields=("result", "skill"), name="unique_result_skill")]


class Certificate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    result = models.OneToOneField(AttemptResult, on_delete=models.PROTECT, related_name="certificate")
    verification_code = models.CharField(max_length=24, unique=True, db_index=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    is_revoked = models.BooleanField(default=False)

    class Meta:
        ordering = ("-issued_at",)

    def __str__(self):
        return self.verification_code

    def get_absolute_url(self):
        return reverse("assessments:certificate", kwargs={"code": self.verification_code})
