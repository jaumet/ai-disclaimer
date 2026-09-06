from django.contrib import admin
from .models import Adhesion, SiteMetric

admin.site.register(SiteMetric)

@admin.register(Adhesion)
class AdhesionAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "supporter_type", "organization_name", "comment_status", "display_publicly", "created_at")
    list_filter = ("comment_status", "supporter_type", "display_publicly", "pledge_version")
    search_fields = ("full_name", "email", "organization_name", "comment")
    readonly_fields = ("comment_status", "comment_review_reason", "pledge_version", "created_at")
