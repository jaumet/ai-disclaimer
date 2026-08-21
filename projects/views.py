from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AdhesionForm, MagicCodeForm, MagicLinkForm, ProjectForm
from .models import Adhesion, MagicLink, PLEDGE_VERSION, PledgeAcceptance, Project


CAMPAIGN_STARTED_ON = date(2026, 8, 21)


def home(request):
    return render(request, "projects/home.html", {
        "projects": Project.objects.filter(is_public=True)[:9],
        "adhesion_count": Adhesion.objects.count(),
        "campaign_target": 100,
        "campaign_progress": min(Adhesion.objects.count(), 100),
        "campaign_started_on": CAMPAIGN_STARTED_ON,
    })


def project_list(request):
    return render(request, "projects/project_list.html", {"projects": Project.objects.filter(is_public=True)})


def badge_guide(request):
    return redirect("/#badges")


def certificate_maker(request):
    return render(request, "projects/certificate_maker.html")


def transparency_pledge(request):
    return render(request, "projects/pledge.html", {"pledge_version": PLEDGE_VERSION})


def site_ai_disclosure(request):
    return render(request, "projects/site_ai_disclosure.html")


def join_initiative(request):
    form = AdhesionForm(request.POST or None)
    joined = False
    if request.method == "POST" and form.is_valid():
        adhesion = form.save(commit=False)
        adhesion.pledge_version = PLEDGE_VERSION
        adhesion.save()
        joined = True
        form = AdhesionForm()
    adhesions = Adhesion.objects.all()
    count = adhesions.count()
    public_adhesions = adhesions.filter(display_publicly=True)
    return render(request, "projects/adhesions.html", {
        "form": form,
        "joined": joined,
        "adhesion_count": count,
        "launch_target": 100,
        "progress_percent": min(count, 100),
        "campaign_started_on": CAMPAIGN_STARTED_ON,
        "public_organizations": public_adhesions.filter(supporter_type="organization"),
        "public_people": public_adhesions.filter(supporter_type="person"),
        "pledge_version": PLEDGE_VERSION,
    })


def _is_local_request(request):
    host = request.get_host().split(":", 1)[0].lower()
    return settings.DEBUG and host in {"localhost", "127.0.0.1"}


def _complete_magic_login(request, link):
    PledgeAcceptance.objects.get_or_create(user=link.user, version=link.pledge_version)
    login(request, link.user, backend="django.contrib.auth.backends.ModelBackend")
    request.session.pop("pending_magic_link_id", None)
    request.session.pop("pending_magic_email", None)
    request.session.pop("pending_magic_code", None)
    messages.success(request, "You’re signed in. Welcome to AI USE DECLARED.")
    return redirect("dashboard")


def request_magic_link(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = MagicLinkForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].strip().lower()
        User = get_user_model()
        user, _ = User.objects.get_or_create(username=email, defaults={"email": email})
        if user.email != email:
            user.email = email
            user.save(update_fields=["email"])
        link, token, code = MagicLink.issue(user)
        url = request.build_absolute_uri(f"/auth/verify/{token}/")
        send_mail("Your AI USE DECLARED sign-in link", f"Sign in to AI USE DECLARED by Selectora:\n\n{url}\n\nVerification code: {code}\n\nBy using this link or code, you confirm the Transparency Pledge (version {PLEDGE_VERSION}). This access expires in 15 minutes and can only be used once.", None, [email])
        is_local = _is_local_request(request)
        if is_local:
            request.session["pending_magic_link_id"] = link.pk
            request.session["pending_magic_email"] = email
            request.session["pending_magic_code"] = code
        return render(request, "registration/link_sent.html", {
            "email": email, "is_local": is_local, "dev_code": code if is_local else None,
            "code_form": MagicCodeForm() if is_local else None,
        })
    return render(request, "registration/magic_link.html", {"form": form})


def verify_magic_link(request, token):
    link = MagicLink.consume(token)
    if not link:
        return render(request, "registration/link_invalid.html", status=400)
    return _complete_magic_login(request, link)


def verify_magic_code(request):
    if request.method != "POST" or not _is_local_request(request):
        raise Http404
    link_id = request.session.get("pending_magic_link_id")
    email = request.session.get("pending_magic_email")
    dev_code = request.session.get("pending_magic_code")
    form = MagicCodeForm(request.POST)
    if link_id and form.is_valid():
        link = MagicLink.consume_code(link_id, form.cleaned_data["code"])
        if link:
            return _complete_magic_login(request, link)
        form.add_error("code", "This code is incorrect, expired or has already been used.")
    elif not link_id:
        form.add_error(None, "Your verification session has expired. Request a new code.")
    return render(request, "registration/link_sent.html", {
        "email": email, "is_local": True, "dev_code": dev_code, "code_form": form,
    }, status=400)


def sign_out(request):
    if request.method == "POST":
        logout(request)
    return redirect("home")


@login_required
def dashboard(request):
    return render(request, "projects/dashboard.html", {"projects": request.user.projects.all()})


@login_required
def project_create(request):
    form = ProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.qualifiers = form.cleaned_data["qualifiers"]
        project.save()
        messages.success(request, "Your project is now registered.")
        return redirect(project)
    return render(request, "projects/project_form.html", {"form": form, "editing": False})


@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.qualifiers = form.cleaned_data["qualifiers"]
        project.save()
        messages.success(request, "Project updated.")
        return redirect(project)
    return render(request, "projects/project_form.html", {"form": form, "editing": True, "project": project})


def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not project.is_public and project.owner != request.user:
        raise Http404
    return render(request, "projects/project_detail.html", {"project": project})


def project_disclosure(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not project.is_public and project.owner != request.user:
        raise Http404
    return render(request, "projects/disclosure_popup.html", {"project": project})
