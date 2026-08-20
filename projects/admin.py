from django.contrib import admin
from .models import MagicLink, PledgeAcceptance, Project

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
