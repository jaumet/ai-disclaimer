from django import forms
from .models import Adhesion, PRIMARY_BADGES, QUALIFIER_BADGES, Project


class AdhesionForm(forms.ModelForm):
    accept_pledge = forms.BooleanField(
        required=True,
        label="I have read and accept the AI USE DECLARED Transparency Pledge.",
        error_messages={"required": "Accept the Transparency Pledge to join the initiative."},
    )

    class Meta:
        model = Adhesion
        fields = ["full_name", "email", "supporter_type", "organization_name", "comment", "display_publicly"]
        labels = {
            "full_name": "Full name",
            "supporter_type": "I am joining as",
            "organization_name": "Organization name",
            "comment": "Comment",
            "display_publicly": "Show my name in the public list of supporters",
        }
        widgets = {
            "full_name": forms.TextInput(attrs={"autocomplete": "name", "placeholder": "Your name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@example.com"}),
            "supporter_type": forms.RadioSelect,
            "organization_name": forms.TextInput(attrs={"autocomplete": "organization", "placeholder": "Only if applicable"}),
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Why do you support the campaign? (optional)"}),
        }

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("supporter_type") == "organization" and not cleaned.get("organization_name", "").strip():
            self.add_error("organization_name", "Enter the organization you are representing.")
        if cleaned.get("supporter_type") == "person":
            cleaned["organization_name"] = ""
        return cleaned


class MagicLinkForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        "placeholder": "you@example.com", "autocomplete": "email", "autofocus": True
    }))
    pledge = forms.BooleanField(
        required=True,
        label="I commit to the AI USE DECLARED Transparency Pledge and to describing my work truthfully.",
        error_messages={"required": "You must accept the Transparency Pledge to continue."},
    )


class MagicCodeForm(forms.Form):
    code = forms.RegexField(
        regex=r"^\d{6}$",
        max_length=6,
        label="Verification code",
        error_messages={"invalid": "Enter the six-digit code shown above."},
        widget=forms.TextInput(attrs={
            "inputmode": "numeric", "autocomplete": "one-time-code", "placeholder": "000000",
            "pattern": "[0-9]{6}", "maxlength": "6", "autofocus": True,
        }),
    )


class ProjectForm(forms.ModelForm):
    qualifiers = forms.MultipleChoiceField(
        choices=QUALIFIER_BADGES, required=False, widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Project
        fields = ["title", "url", "description", "primary_badge", "qualifiers", "tools_used", "process_note", "is_public"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Project name"}),
            "url": forms.URLInput(attrs={"placeholder": "https://example.com"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "What is it, and who is it for?"}),
            "primary_badge": forms.RadioSelect,
            "tools_used": forms.TextInput(attrs={"placeholder": "e.g. Claude, Stable Diffusion, no AI tools"}),
            "process_note": forms.Textarea(attrs={"rows": 4, "placeholder": "Briefly explain how AI was or was not used."}),
        }

    def clean(self):
        cleaned = super().clean()
        primary = cleaned.get("primary_badge")
        qualifiers = set(cleaned.get("qualifiers") or [])
        ai_qualifiers = qualifiers - {"human-reviewed"}
        if primary in {"no-ai-used", "no-generative-ai"} and ai_qualifiers:
            self.add_error("qualifiers", "This primary badge can only be combined with HUMAN-REVIEWED.")
        return cleaned
