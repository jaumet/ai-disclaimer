from datetime import date

from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .email import send_adhesion_confirmation
from .forms import AdhesionForm
from .models import Adhesion, PLEDGE_VERSION, SiteMetric


CAMPAIGN_STARTED_ON = date(2026, 8, 21)
BADGE_CONFIGURATION_KEY = "badge_configurations"
BADGE_CONFIGURATION_INITIAL_VALUE = 123


def badge_configuration_count():
    metric, _ = SiteMetric.objects.get_or_create(
        key=BADGE_CONFIGURATION_KEY,
        defaults={"value": BADGE_CONFIGURATION_INITIAL_VALUE},
    )
    return metric.value


def home(request):
    return render(request, "projects/home.html", {
        "adhesion_count": Adhesion.objects.count(),
        "badge_configuration_count": badge_configuration_count(),
        "primary_badge_summary": [
            ("badges/primary/01-ai-made.png", "AI-Made"),
            ("badges/primary/02-ai-assisted.png", "AI-Assisted"),
            ("badges/primary/03-ai-edited.png", "AI-Edited"),
            ("badges/primary/04-no-generative-ai.png", "No Generative AI"),
            ("badges/primary/05-no-ai-used.png", "No AI Used"),
        ],
        "qualifier_badge_summary": [
            ("badges/secondary/01-human-reviewed.png", "Human-Reviewed"),
            ("badges/secondary/02-ai-translated.png", "AI-Translated"),
            ("badges/secondary/03-synthetic-voice.png", "Synthetic Voice"),
            ("badges/secondary/04-ai-generated-images.png", "AI-Generated Images"),
            ("badges/secondary/05-ai-generated-code.png", "AI-Generated Code"),
            ("badges/secondary/06-ai-generated-video.svg", "AI-Generated Video"),
            ("badges/secondary/07-ai-generated-text.svg", "AI-Generated Text"),
        ],
    })


def badge_guide(request):
    return render(request, "projects/badge_guide.html")


@ensure_csrf_cookie
def declaration_maker(request):
    return render(request, "projects/certificate_maker.html")


@require_POST
def record_badge_configuration(request):
    metric, _ = SiteMetric.objects.get_or_create(
        key=BADGE_CONFIGURATION_KEY,
        defaults={"value": BADGE_CONFIGURATION_INITIAL_VALUE},
    )
    SiteMetric.objects.filter(pk=metric.pk).update(value=F("value") + 1)
    metric.refresh_from_db(fields=["value"])
    return JsonResponse({"count": metric.value})


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
        send_adhesion_confirmation(adhesion)
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


def legacy_declaration_redirect(request, *args, **kwargs):
    """Keep old public links useful without retaining project or account records."""
    return redirect("declaration_maker", permanent=True)
