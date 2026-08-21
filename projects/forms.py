from django import forms
from .models import Adhesion


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
