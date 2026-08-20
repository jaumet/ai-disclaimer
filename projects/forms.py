from django import forms
from .models import PRIMARY_BADGES, QUALIFIER_BADGES, Project


class MagicLinkForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        "placeholder": "you@example.com", "autocomplete": "email", "autofocus": True
    }))
    pledge = forms.BooleanField(
        required=True,
        label="I commit to the AI USE: DECLARED Transparency Pledge and to describing my work truthfully.",
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
