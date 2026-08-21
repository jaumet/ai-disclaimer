from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("badges/", views.badge_guide, name="badge_guide"),
    path("create-declaration/", views.certificate_maker, name="certificate_maker"),
    path("made-openly/", views.project_list, name="project_list"),
    path("transparency-pledge/", views.transparency_pledge, name="transparency_pledge"),
    path("ai-use/", views.site_ai_disclosure, name="site_ai_disclosure"),
    path("join/", views.join_initiative, name="join_initiative"),
    path("auth/sign-in/", views.request_magic_link, name="request_magic_link"),
    path("auth/verify/<str:token>/", views.verify_magic_link, name="verify_magic_link"),
    path("auth/verify-code/", views.verify_magic_code, name="verify_magic_code"),
    path("auth/sign-out/", views.sign_out, name="sign_out"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("projects/new/", views.project_create, name="project_create"),
    path("projects/<uuid:pk>/", views.project_detail, name="project_detail"),
    path("projects/<uuid:pk>/disclosure/", views.project_disclosure, name="project_disclosure"),
    path("projects/<uuid:pk>/edit/", views.project_edit, name="project_edit"),
]
