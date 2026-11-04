import os
from pathlib import Path
from typing import Optional

import resend
from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(BACKEND_DIR.parent / ".env")


class EmailConfigurationError(RuntimeError):
    """Raised when the transactional email service is not configured."""


def _required_setting(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise EmailConfigurationError(f"{name} doit etre defini.")
    return value


def _sender() -> str:
    email = _required_setting("RESEND_FROM_EMAIL")
    name = os.getenv("RESEND_FROM_NAME", "RuinionAI").strip()
    return f"{name} <{email}>" if name else email


async def send_email(
    to: str,
    subject: str,
    html: str,
    *,
    text: Optional[str] = None,
    reply_to: Optional[str] = None,
) -> resend.Emails.SendResponse:
    """Send one transactional email through Resend.

    Configuration errors and Resend delivery errors are deliberately allowed to
    propagate so callers can log them or offer a retry without reporting a
    successful delivery.
    """
    recipient = to.strip()
    email_subject = subject.strip()
    if not recipient:
        raise ValueError("Le destinataire de l'e-mail est obligatoire.")
    if not email_subject:
        raise ValueError("L'objet de l'e-mail est obligatoire.")
    if not html.strip():
        raise ValueError("Le contenu HTML de l'e-mail est obligatoire.")

    resend.api_key = _required_setting("RESEND_API_KEY")

    params: resend.Emails.SendParams = {
        "from": _sender(),
        "to": [recipient],
        "subject": email_subject,
        "html": html,
    }

    plain_text = text.strip() if text else ""
    if plain_text:
        params["text"] = plain_text

    configured_reply_to = (
        reply_to.strip()
        if reply_to
        else os.getenv("RESEND_REPLY_TO", "").strip()
    )
    if configured_reply_to:
        params["reply_to"] = configured_reply_to

    return await resend.Emails.send_async(params)
