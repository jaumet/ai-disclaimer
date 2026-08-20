from django.contrib import admin
from .models import Adhesion, MagicLink, PledgeAcceptance, Project

@admin.register(Adhesion)
class AdhesionAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "supporter_type", "organization_name", "comment_status", "display_publicly", "created_at")
    list_filter = ("comment_status", "supporter_type", "display_publicly", "pledge_version")
    search_fields = ("full_name", "email", "organization_name", "comment")
    readonly_fields = ("comment_status", "comment_review_reason", "pledge_version", "created_at")

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "primary_badge", "is_public", "created_at")
    list_filter = ("primary_badge", "is_public")
    search_fields = ("title", "description", "owner__email")

@admin.register(MagicLink)
class MagicLinkAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "expires_at", "used_at")
    readonly_fields = ("token_hash", "created_at")

@admin.register(PledgeAcceptance)
class PledgeAcceptanceAdmin(admin.ModelAdmin):
    list_display = ("user", "version", "accepted_at")
    readonly_fields = ("user", "version", "accepted_at")
