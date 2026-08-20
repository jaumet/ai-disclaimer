import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import ProjectForm
from .models import PledgeAcceptance, Project


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
        self.client.logout()
        response = self.client.get(project.get_absolute_url())
        self.assertNotContains(response, "OWNER TOOLS")
        self.assertNotContains(response, "Download PNG")

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
        for name in ("badge_guide", "certificate_maker", "project_list", "transparency_pledge"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

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
