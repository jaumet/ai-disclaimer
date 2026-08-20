import hashlib
import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


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


class PledgeAcceptance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pledge_acceptances")
    version = models.CharField(max_length=20, default=PLEDGE_VERSION)
    accepted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "version"], name="unique_pledge_acceptance")]

    def __str__(self):
        return f"{self.user} — pledge {self.version}"


class MagicLink(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token_hash = models.CharField(max_length=64, unique=True)
    # Empty only for magic links created before local codes were introduced.
    code_hash = models.CharField(max_length=64, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    pledge_version = models.CharField(max_length=20, default=PLEDGE_VERSION)

    @classmethod
    def issue(cls, user):
        raw_token = secrets.token_urlsafe(32)
        raw_code = f"{secrets.randbelow(1_000_000):06d}"
        link = cls.objects.create(
            user=user,
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            code_hash=hashlib.sha256(raw_code.encode()).hexdigest(),
            expires_at=timezone.now() + timedelta(minutes=15),
        )
        return link, raw_token, raw_code

    @classmethod
    def consume(cls, raw_token):
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        link = cls.objects.select_related("user").filter(
            token_hash=token_hash, used_at__isnull=True, expires_at__gt=timezone.now()
        ).first()
        if link:
            link.used_at = timezone.now()
            link.save(update_fields=["used_at"])
        return link

    @classmethod
    def consume_code(cls, link_id, raw_code):
        code_hash = hashlib.sha256(raw_code.encode()).hexdigest()
        link = cls.objects.select_related("user").filter(
            pk=link_id, code_hash=code_hash, used_at__isnull=True, expires_at__gt=timezone.now()
        ).first()
        if link:
            link.used_at = timezone.now()
            link.save(update_fields=["used_at"])
        return link


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects")
    title = models.CharField(max_length=120)
    url = models.URLField()
    description = models.TextField(max_length=600)
    primary_badge = models.CharField(max_length=30, choices=PRIMARY_BADGES)
    qualifiers = models.JSONField(default=list, blank=True)
    tools_used = models.CharField(max_length=300, blank=True, help_text="Optional — e.g. ChatGPT, Midjourney, no AI tools")
    process_note = models.TextField(max_length=800, blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("project_detail", args=[self.pk])

    @property
    def primary_image(self):
        number = dict(zip([x[0] for x in PRIMARY_BADGES], ["01", "02", "03", "04", "05"]))[self.primary_badge]
        return f"badges/primary/{number}-{self.primary_badge}.png"

    @property
    def qualifier_data(self):
        labels = dict(QUALIFIER_BADGES)
        images = {
            key: f"badges/secondary/{i:02}-{key}.{'svg' if i > 5 else 'png'}"
            for i, (key, _) in enumerate(QUALIFIER_BADGES, 1)
        }
        return [{"key": key, "label": labels[key], "image": images[key]}
                for key in self.qualifiers if key in labels]
