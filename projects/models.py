from django.db import models


PRIMARY_BADGES = [
    ("ai-made", "AI-MADE"),
    ("ai-assisted", "AI-ASSISTED"),
    ("ai-edited", "AI-EDITED"),
    ("no-generative-ai", "NO GENERATIVE AI"),
    ("no-ai-used", "NO AI USED"),
]

QUALIFIER_BADGES = [
    ("human-reviewed", "HUMAN-REVIEWED"),
    ("ai-translated", "AI-TRANSLATED"),
    ("synthetic-voice", "SYNTHETIC VOICE"),
    ("ai-generated-images", "AI-GENERATED IMAGES"),
    ("ai-generated-code", "AI-GENERATED CODE"),
    ("ai-generated-video", "AI-GENERATED VIDEO"),
    ("ai-generated-text", "AI-GENERATED TEXT"),
]

PLEDGE_VERSION = "1.0"


class SiteMetric(models.Model):
    key = models.CharField(max_length=50, unique=True)
    value = models.PositiveBigIntegerField(default=0)

    def __str__(self):
        return f"{self.key}: {self.value}"


class Adhesion(models.Model):
    SUPPORTER_TYPES = [("person", "A person"), ("organization", "An organization")]
    COMMENT_STATUSES = [("clean", "OK"), ("needs_review", "NEEDS REVIEW")]

    full_name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    supporter_type = models.CharField(max_length=20, choices=SUPPORTER_TYPES, default="person")
    organization_name = models.CharField(max_length=160, blank=True)
    comment = models.TextField(max_length=600, blank=True)
    comment_status = models.CharField(max_length=20, choices=COMMENT_STATUSES, default="clean")
    comment_review_reason = models.CharField(max_length=120, blank=True)
    display_publicly = models.BooleanField(default=True)
    pledge_version = models.CharField(max_length=20, default=PLEDGE_VERSION)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.organization_name or self.full_name

    def save(self, *args, **kwargs):
        from .moderation import review_comment

        needs_review, reason = review_comment(self.comment)
        self.comment_status = "needs_review" if needs_review else "clean"
        self.comment_review_reason = reason
        super().save(*args, **kwargs)

    @property
    def public_label(self):
        return self.organization_name or self.full_name
