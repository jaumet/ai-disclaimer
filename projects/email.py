import logging

from django.conf import settings
from django.core.mail import send_mail


logger = logging.getLogger(__name__)


def send_adhesion_confirmation(adhesion):
    """Send one confirmation after an adhesion is saved, without affecting it on failure."""
    subject = "Thank you for supporting AI Use Declared"
    body = (
        f"Hello {adhesion.full_name},\n\n"
        "Thank you for supporting AI Use Declared and accepting version "
        f"{adhesion.pledge_version} of the Transparency Pledge.\n\n"
        "Your support has been recorded.\n\n"
        "https://ai.selectora.cc/\n\n"
        "AI Use Declared\n"
    )

    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [adhesion.email],
            fail_silently=False,
        )
    except Exception as error:  # The saved adhesion must survive temporary email failures.
        logger.error(
            "Could not send adhesion confirmation (adhesion_id=%s, error_type=%s).",
            adhesion.pk,
            type(error).__name__,
        )
        return False
    return True
