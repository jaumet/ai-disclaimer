import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import ProjectForm
from .models import Adhesion, PledgeAcceptance, Project


class AdhesionTests(TestCase):
    def test_joining_needs_no_account_and_accepts_pledge(self):
        response = self.client.post(reverse("join_initiative"), {
            "full_name": "Open Maker",
            "email": "Maker@Example.com",
            "supporter_type": "person",
            "display_publicly": "on",
            "accept_pledge": "on",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You’re part of it")
        adhesion = Adhesion.objects.get()
        self.assertEqual(adhesion.email, "maker@example.com")
        self.assertEqual(adhesion.pledge_version, "1.0")
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_pledge_and_organization_name_are_required(self):
        response = self.client.post(reverse("join_initiative"), {
            "full_name": "Open Org", "email": "org@example.com", "supporter_type": "organization",
        })
        self.assertContains(response, "Enter the organization")
        self.assertContains(response, "Accept the Transparency Pledge")
        self.assertFalse(Adhesion.objects.exists())

    def test_campaign_lists_public_organizations_before_people(self):
        Adhesion.objects.create(full_name="Private", email="private@example.com", display_publicly=False)
        Adhesion.objects.create(full_name="Person", email="person@example.com", supporter_type="person")
        Adhesion.objects.create(full_name="Org Contact", email="org@example.com", supporter_type="organization", organization_name="Open Org")
        response = self.client.get(reverse("join_initiative"))
        self.assertContains(response, "Campaign started")
        self.assertContains(response, "3 TOTAL")
        self.assertLess(response.content.index(b"Open Org"), response.content.index(b"Person"))
        self.assertNotContains(response, ">Private<")

    def test_comment_is_saved_and_suspicious_wording_is_flagged(self):
        response = self.client.post(reverse("join_initiative"), {
            "full_name": "Concerned Maker", "email": "comment@example.com",
            "supporter_type": "person", "comment": "This is fucking spam", "accept_pledge": "on",
        })
        self.assertEqual(response.status_code, 200)
        adhesion = Adhesion.objects.get()
        self.assertEqual(adhesion.comment, "This is fucking spam")
        self.assertEqual(adhesion.comment_status, "needs_review")
        self.assertEqual(adhesion.comment_review_reason, "Potentially offensive wording")

    def test_normal_comment_is_marked_ok(self):
        adhesion = Adhesion.objects.create(
            full_name="Supporter", email="supporter@example.com",
            comment="Transparent creative work deserves public support.",
        )
        self.assertEqual(adhesion.comment_status, "clean")
        self.assertEqual(adhesion.comment_review_reason, "")


class MagicLinkTests(TestCase):
    def test_magic_link_creates_user_and_signs_in_once(self):
        response = self.client.post(reverse("request_magic_link"), {"email": "Maker@Example.com", "pledge": "on"})
        self.assertContains(response, "Check your inbox")
        self.assertEqual(get_user_model().objects.get().email, "maker@example.com")
        self.assertEqual(PledgeAcceptance.objects.count(), 0)
        url = re.search(r"http://testserver(/auth/verify/[^\s]+/)", mail.outbox[0].body).group(1)
        response = self.client.get(url)
        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(PledgeAcceptance.objects.count(), 1)
        self.assertIn("_auth_user_id", self.client.session)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 400)

    @override_settings(DEBUG=True)
    def test_local_request_shows_code_and_accepts_it(self):
        response = self.client.post(
            reverse("request_magic_link"), {"email": "local@example.com", "pledge": "on"},
            HTTP_HOST="localhost",
        )
        self.assertContains(response, "LOCAL ACCESS CODE")
        code = response.context["dev_code"]
        self.assertRegex(code, r"^\d{6}$")
        response = self.client.post(reverse("verify_magic_code"), {"code": code}, HTTP_HOST="localhost")
        self.assertRedirects(response, reverse("dashboard"))
        self.assertIn("_auth_user_id", self.client.session)


class ProjectTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="owner@example.com", email="owner@example.com")
        self.client.force_login(self.user)

    def test_project_creation(self):
        response = self.client.post(reverse("project_create"), {
            "title": "Clear Project",
            "url": "https://example.com",
            "description": "A transparent digital project.",
            "primary_badge": "ai-assisted",
            "qualifiers": ["human-reviewed", "ai-generated-code"],
            "tools_used": "Claude",
            "process_note": "A human directed and reviewed generated code.",
            "is_public": "on",
        })
        project = Project.objects.get()
        self.assertRedirects(response, project.get_absolute_url())
        self.assertEqual(project.qualifiers, ["human-reviewed", "ai-generated-code"])
        response = self.client.get(project.get_absolute_url())
        self.assertContains(response, "OWNER TOOLS")
        self.assertContains(response, "Download PNG")

    def test_certificate_tools_are_only_visible_to_owner(self):
        project = Project.objects.create(owner=self.user, title="Public", url="https://example.com",
                                         description="Public project", primary_badge="ai-assisted", is_public=True)
        disclosure_url = reverse("project_disclosure", args=[project.pk])
        disclosure = self.client.get(disclosure_url)
        self.assertContains(disclosure, "This project discloses its use of AI as")
        self.assertContains(disclosure, "AI-ASSISTED")
        self.client.logout()
        response = self.client.get(project.get_absolute_url())
        self.assertNotContains(response, "OWNER TOOLS")
        self.assertNotContains(response, "Download PNG")
        self.assertEqual(self.client.get(disclosure_url).status_code, 200)

    def test_registration_form_renders_all_badges(self):
        response = self.client.get(reverse("project_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "01-ai-made.png")
        self.assertContains(response, "05-no-ai-used.png")
        self.assertContains(response, "01-human-reviewed.png")
        self.assertContains(response, "05-ai-generated-code.png")
        self.assertContains(response, "06-ai-generated-video.svg")
        self.assertContains(response, "07-ai-generated-text.svg")

    def test_public_guide_registry_and_pledge_render(self):
        self.client.logout()
        for name in ("badge_guide", "certificate_maker", "project_list", "transparency_pledge", "site_ai_disclosure"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "aiud-details-ai-use-declared")
            self.assertContains(response, reverse("site_ai_disclosure"))
            self.assertNotContains(response, "688b4cbc-6bb2-47d9-9336-78cff1bfb575")
            self.assertContains(response, "02-ai-assisted.png")
            self.assertContains(response, "01-human-reviewed.png")

        home = self.client.get(reverse("home"))
        self.assertContains(home, "TTS-AI-transparency-declaration.mp3")
        self.assertNotContains(home, "CLEAR DISCLOSURE")
        self.assertContains(home, "Beyond detection:")
        self.assertContains(home, "eur-lex.europa.eu/eli/reg/2024/1689/oj/eng")
        self.assertContains(home, "complement—not replace")
        pledge = self.client.get(reverse("transparency_pledge"))
        self.assertEqual(pledge.content.count(b"<audio"), 1)

    def test_no_ai_rejects_ai_qualifier(self):
        form = ProjectForm(data={
            "title": "Human Project", "url": "https://example.com", "description": "Made by people.",
            "primary_badge": "no-ai-used", "qualifiers": ["ai-generated-images"], "is_public": "on",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("can only be combined", str(form.errors))

    def test_private_project_is_hidden_from_other_users(self):
        project = Project.objects.create(owner=self.user, title="Private", url="https://example.com",
                                         description="Private project", primary_badge="no-ai-used", is_public=False)
        self.client.logout()
        self.assertEqual(self.client.get(project.get_absolute_url()).status_code, 404)
