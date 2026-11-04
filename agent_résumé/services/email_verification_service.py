import logging
import os
from datetime import datetime, timedelta
from hashlib import sha256
from html import escape
from secrets import token_urlsafe
from urllib.parse import quote

from sqlalchemy.orm import Session

from models import EmailVerificationToken, User
from services.email_service import send_email


logger = logging.getLogger(__name__)
DEFAULT_EXPIRATION_HOURS = 24


def verification_expiration_hours() -> int:
    raw_value = os.getenv(
        "EMAIL_VERIFICATION_EXPIRE_HOURS",
        str(DEFAULT_EXPIRATION_HOURS),
    ).strip()
    try:
        value = int(raw_value)
    except ValueError as error:
        raise RuntimeError(
            "EMAIL_VERIFICATION_EXPIRE_HOURS doit être un entier."
        ) from error
    if not 1 <= value <= 168:
        raise RuntimeError(
            "EMAIL_VERIFICATION_EXPIRE_HOURS doit être compris entre 1 et 168."
        )
    return value


def create_email_verification_token(
    db: Session,
    user: User,
    *,
    now: datetime | None = None,
) -> str:
    current_time = now or datetime.utcnow()
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id,
        EmailVerificationToken.used_at.is_(None),
    ).update(
        {EmailVerificationToken.used_at: current_time},
        synchronize_session=False,
    )

    token = token_urlsafe(32)
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=sha256(token.encode("utf-8")).hexdigest(),
            expires_at=current_time
            + timedelta(hours=verification_expiration_hours()),
        )
    )
    return token


def verification_url(token: str) -> str:
    frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")
    if not frontend_url:
        raise RuntimeError("FRONTEND_URL doit être défini.")
    # Le fragment n'est pas transmis au serveur web et n'apparait donc pas dans
    # les journaux d'acces HTTP. Le frontend le retire apres validation.
    return f"{frontend_url}/verifier-email#token={quote(token, safe='')}"


async def send_welcome_verification_email(
    email: str,
    first_name: str,
    token: str,
) -> None:
    link = verification_url(token)
    safe_name = escape(first_name.strip() or "bonjour")
    safe_link = escape(link, quote=True)
    html = f"""
    <!doctype html>
    <html lang="fr">
      <body style="margin:0;background:#f8fafc;font-family:Arial,sans-serif;color:#0f172a">
        <div style="max-width:600px;margin:0 auto;padding:40px 20px">
          <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;padding:36px">
            <h1 style="margin:0 0 20px;font-size:28px">Bienvenue sur RuinionAI</h1>
            <p>Bonjour {safe_name},</p>
            <p>Votre espace est créé. Confirmez maintenant votre adresse e-mail pour pouvoir vous connecter.</p>
            <p style="margin:30px 0">
              <a href="{safe_link}" style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;padding:14px 22px;border-radius:9px;font-weight:700">
                Vérifier mon adresse e-mail
              </a>
            </p>
            <p style="font-size:14px;color:#64748b">Ce lien expire dans {verification_expiration_hours()} heures et ne peut être utilisé qu'une seule fois.</p>
            <p style="font-size:13px;color:#94a3b8;word-break:break-all">Si le bouton ne fonctionne pas : {safe_link}</p>
          </div>
        </div>
      </body>
    </html>
    """
    text = (
        f"Bonjour {first_name.strip() or 'bonjour'},\n\n"
        "Bienvenue sur RuinionAI. Confirmez votre adresse e-mail en ouvrant "
        f"ce lien :\n{link}\n\n"
        f"Ce lien expire dans {verification_expiration_hours()} heures."
    )
    await send_email(
        email,
        "Bienvenue sur RuinionAI - vérifiez votre adresse",
        html,
        text=text,
    )


async def send_welcome_email(email: str, first_name: str) -> None:
    safe_name = escape(first_name.strip() or "bonjour")
    html = f"""
    <!doctype html>
    <html lang="fr">
      <body style="margin:0;background:#f8fafc;font-family:Arial,sans-serif;color:#0f172a">
        <div style="max-width:600px;margin:0 auto;padding:40px 20px">
          <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;padding:36px">
            <h1 style="margin:0 0 20px;font-size:28px">Bienvenue sur RuinionAI</h1>
            <p>Bonjour {safe_name},</p>
            <p>Votre compte est prêt. Vous pouvez maintenant retrouver votre équipe et vos réunions dans votre espace.</p>
          </div>
        </div>
      </body>
    </html>
    """
    text = (
        f"Bonjour {first_name.strip() or 'bonjour'},\n\n"
        "Bienvenue sur RuinionAI. Votre compte est prêt."
    )
    await send_email(
        email,
        "Bienvenue sur RuinionAI",
        html,
        text=text,
    )


async def deliver_welcome_verification_email(
    email: str,
    first_name: str,
    token: str,
) -> None:
    try:
        await send_welcome_verification_email(email, first_name, token)
    except Exception:
        logger.exception("Echec de l'envoi de l'e-mail de verification.")


async def deliver_welcome_email(email: str, first_name: str) -> None:
    try:
        await send_welcome_email(email, first_name)
    except Exception:
        logger.exception("Echec de l'envoi de l'e-mail de bienvenue.")
