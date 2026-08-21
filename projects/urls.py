from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("badges/", views.badge_guide, name="badge_guide"),
    path("create-declaration/", views.declaration_maker, name="declaration_maker"),
    path("transparency-pledge/", views.transparency_pledge, name="transparency_pledge"),
    path("ai-use/", views.site_ai_disclosure, name="site_ai_disclosure"),
    path("join/", views.join_initiative, name="join_initiative"),
    # Compatibility redirects for links created by the earlier registry/account version.
    path("made-openly/", views.legacy_declaration_redirect),
    path("auth/sign-in/", views.legacy_declaration_redirect),
    path("auth/verify/<str:token>/", views.legacy_declaration_redirect),
    path("auth/verify-code/", views.legacy_declaration_redirect),
    path("auth/sign-out/", views.legacy_declaration_redirect),
    path("dashboard/", views.legacy_declaration_redirect),
    path("projects/new/", views.legacy_declaration_redirect),
    path("projects/<uuid:pk>/", views.legacy_declaration_redirect),
    path("projects/<uuid:pk>/disclosure/", views.legacy_declaration_redirect),
    path("projects/<uuid:pk>/edit/", views.legacy_declaration_redirect),
]
