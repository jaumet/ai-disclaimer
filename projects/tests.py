import os
import subprocess
import sys
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .models import Adhesion


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
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
        self.assertEqual(len(mail.outbox), 1)
        confirmation = mail.outbox[0]
        self.assertEqual(confirmation.to, ["maker@example.com"])
        self.assertEqual(confirmation.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(confirmation.subject, "Thank you for supporting AI Use Declared")
        self.assertIn("Hello Open Maker,", confirmation.body)
        self.assertIn("version 1.0 of the Transparency Pledge", confirmation.body)
        self.assertIn("Your support has been recorded.", confirmation.body)
        self.assertIn("https://ai.selectora.cc/", confirmation.body)

    def test_pledge_and_organization_name_are_required(self):
        response = self.client.post(reverse("join_initiative"), {
            "full_name": "Open Org", "email": "org@example.com", "supporter_type": "organization",
        })
        self.assertContains(response, "Enter the organization")
        self.assertContains(response, "Accept the Transparency Pledge")
        self.assertFalse(Adhesion.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_duplicate_email_does_not_send_a_second_confirmation(self):
        data = {
            "full_name": "One Supporter",
            "email": "same@example.com",
            "supporter_type": "person",
            "accept_pledge": "on",
        }
        self.assertEqual(self.client.post(reverse("join_initiative"), data).status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        duplicate = {**data, "full_name": "Duplicate Supporter"}
        response = self.client.post(reverse("join_initiative"), duplicate)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Adhesion.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    @patch("projects.email.send_mail", side_effect=RuntimeError("temporary backend failure"))
    def test_email_backend_failure_does_not_remove_adhesion_or_return_500(self, mocked_send):
        with self.assertLogs("projects.email", level="ERROR") as captured:
            response = self.client.post(reverse("join_initiative"), {
                "full_name": "Saved Supporter",
                "email": "saved@example.com",
                "supporter_type": "person",
                "accept_pledge": "on",
            })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You’re part of it")
        self.assertTrue(Adhesion.objects.filter(email="saved@example.com").exists())
        mocked_send.assert_called_once()
        self.assertIn("error_type=RuntimeError", captured.output[0])
        self.assertNotIn("saved@example.com", captured.output[0])

    def test_campaign_lists_public_organizations_before_people(self):
        Adhesion.objects.create(full_name="Private", email="private@example.com", display_publicly=False)
        Adhesion.objects.create(full_name="Person", email="person@example.com", supporter_type="person")
        Adhesion.objects.create(full_name="Org Contact", email="org@example.com", supporter_type="organization", organization_name="Open Org")
        response = self.client.get(reverse("join_initiative"))
        self.assertContains(response, "3 TOTAL")
        self.assertNotContains(response, "founding supporters")
        self.assertNotContains(response, "Campaign started")
        self.assertLess(response.content.index(b"Open Org"), response.content.index(b"Person"))
        self.assertNotContains(response, ">Private<")

    def test_campaign_milestones_appear_from_one_hundred_supporters(self):
        Adhesion.objects.bulk_create([
            Adhesion(full_name=f"Supporter {number}", email=f"supporter{number}@example.com")
            for number in range(100)
        ])
        response = self.client.get(reverse("join_initiative"))
        self.assertContains(response, "of 100 founding supporters")
        self.assertContains(response, "Campaign started August 21, 2026")

    def test_suspicious_comment_is_flagged(self):
        Adhesion.objects.create(
            full_name="Concerned Maker", email="comment@example.com", comment="This is fucking spam"
        )
        adhesion = Adhesion.objects.get()
        self.assertEqual(adhesion.comment_status, "needs_review")
        self.assertEqual(adhesion.comment_review_reason, "Potentially offensive wording")


class PublicSiteTests(TestCase):
    def test_core_pages_render_without_account_links(self):
        for name in ("home", "badge_guide", "declaration_maker", "transparency_pledge", "site_ai_disclosure", "join_initiative"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, "Sign in")
            self.assertNotContains(response, "Register a project")

    def test_home_centres_creation_and_support(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Choose your AI badges")
        self.assertContains(response, "Support the initiative")
        self.assertContains(response, "Beyond marking:")
        self.assertContains(response, "A voluntary act of intellectual honesty")
        self.assertContains(response, "machine-readable marking")
        self.assertContains(response, "different, complementary purpose")
        self.assertContains(response, "complements—not replaces")
        self.assertNotContains(response, "Recently declared")
        self.assertNotContains(response, "See declared projects")
        self.assertNotContains(response, "PUBLIC REGISTRY")
        content = response.content
        self.assertLess(content.index(b'class="hero home-hero"'), content.index(b'id="how-it-works"'))
        self.assertLess(content.index(b'id="how-it-works"'), content.index(b'class="support-initiative"'))
        self.assertLess(content.index(b'class="support-initiative"'), content.index(b'class="beyond-detection'))
        self.assertLess(content.index(b'class="beyond-detection'), content.index(b'class="home-pledge-section"'))
        self.assertLess(content.index(b'class="home-pledge-section"'), content.index(b'class="cta-band"'))
        self.assertEqual(content.count(b"<audio"), 1)
        self.assertContains(response, 'class="button button-small nav-badges"')
        self.assertContains(response, "It does not imply independent verification or certification")
        self.assertNotContains(response, "A SHARED COMMITMENT")

    def test_maker_is_anonymous_and_has_all_badges(self):
        response = self.client.get(reverse("declaration_maker"))
        self.assertContains(response, "Nothing is uploaded or saved")
        self.assertNotContains(response, "Project or website name")
        self.assertNotContains(response, "Website URL")
        self.assertContains(response, "01-ai-made.png")
        self.assertContains(response, "05-no-ai-used.png")
        self.assertContains(response, "06-ai-generated-video.svg")
        self.assertContains(response, "07-ai-generated-text.svg")
        self.assertNotContains(response, 'data-src="/static/badges/primary/02-ai-assisted.png" checked')
        self.assertContains(response, "Choose the main AI use")
        self.assertContains(response, "Choose secondary uses and details")
        self.assertContains(response, "Choose the style")
        self.assertContains(response, "Download or embed")
        self.assertContains(response, "Download PNG")
        self.assertContains(response, "Download SVG")
        self.assertContains(response, "Copy generated HTML")

    def test_old_registry_and_account_urls_redirect_to_maker(self):
        for path in ("/made-openly/", "/auth/sign-in/", "/dashboard/", "/projects/new/"):
            response = self.client.get(path)
            self.assertRedirects(response, reverse("declaration_maker"), status_code=301)

    def test_admin_login_remains_available(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)


class EmailSettingsTests(SimpleTestCase):
    def _settings_process(self, email_backend):
        environment = os.environ.copy()
        environment.pop("RESEND_API_KEY", None)
        environment.pop("DEFAULT_FROM_EMAIL", None)
        environment["EMAIL_BACKEND"] = email_backend
        environment["DJANGO_SETTINGS_MODULE"] = "config.settings"
        return subprocess.run(
            [
                sys.executable,
                "-c",
                "import django; django.setup(); "
                "from django.conf import settings; "
                "assert settings.DEFAULT_FROM_EMAIL == "
                "'AI Use Declared <noreply@selectora.cc>'",
            ],
            cwd=settings.BASE_DIR,
            env=environment,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )

    def test_console_backend_loads_without_resend_api_key(self):
        result = self._settings_process("django.core.mail.backends.console.EmailBackend")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_smtp_backend_requires_resend_api_key(self):
        result = self._settings_process("django.core.mail.backends.smtp.EmailBackend")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "RESEND_API_KEY is required when the SMTP email backend is enabled.",
            result.stderr + result.stdout,
        )
