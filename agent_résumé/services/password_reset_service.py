import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from html import escape
from uuid import uuid4

import jwt
from sqlalchemy.orm import Session

from auth.security import ALGORITHM, SECRET_KEY, TOKEN_AUDIENCE, TOKEN_ISSUER
from models import PasswordResetCode, User
from services.email_service import send_email


logger = logging.getLogger(__name__)
DEFAULT_EXPIRATION_MINUTES = 10


class InvalidPasswordResetToken(ValueError):
    pass


def reset_code_expiration_minutes() -> int:
    raw_value = os.getenv(
        "PASSWORD_RESET_CODE_EXPIRE_MINUTES",
        str(DEFAULT_EXPIRATION_MINUTES),
    ).strip()
    try:
        value = int(raw_value)
    except ValueError as error:
        raise RuntimeError(
            "PASSWORD_RESET_CODE_EXPIRE_MINUTES doit être un entier."
        ) from error
    if not 5 <= value <= 30:
        raise RuntimeError(
            "PASSWORD_RESET_CODE_EXPIRE_MINUTES doit être compris entre 5 et 30."
        )
    return value


def hash_reset_code(user_id: int, code: str) -> str:
    payload = f"{user_id}:{code}".encode("utf-8")
    return hmac.new(SECRET_KEY.encode("utf-8"), payload, sha256).hexdigest()


def create_password_reset_token(user: User, reset_code_id: int) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=reset_code_expiration_minutes())
    payload = {
        "sub": str(user.id),
        "ver": int(user.token_version),
        "reset_code_id": int(reset_code_id),
        "jti": uuid4().hex,
        "typ": "password_reset",
        "iss": TOKEN_ISSUER,
        "aud": TOKEN_AUDIENCE,
        "iat": now,
        "exp": expires_at,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_password_reset_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=TOKEN_AUDIENCE,
            issuer=TOKEN_ISSUER,
            options={
                "require": [
                    "sub",
                    "ver",
                    "reset_code_id",
                    "jti",
                    "typ",
                    "iat",
                    "exp",
                    "iss",
                    "aud",
                ],
            },
        )
    except jwt.PyJWTError as error:
        raise InvalidPasswordResetToken from error

    if payload.get("typ") != "password_reset":
        raise InvalidPasswordResetToken
    return payload


def create_password_reset_code(
    db: Session,
    user: User,
    *,
    now: datetime | None = None,
) -> str:
    current_time = now or datetime.utcnow()
    db.query(PasswordResetCode).filter(
        PasswordResetCode.user_id == user.id,
        PasswordResetCode.used_at.is_(None),
    ).update(
        {PasswordResetCode.used_at: current_time},
        synchronize_session=False,
    )

    code = f"{secrets.randbelow(100_000_000):08d}"
    db.add(
        PasswordResetCode(
            user_id=user.id,
            code_hash=hash_reset_code(user.id, code),
            expires_at=current_time
            + timedelta(minutes=reset_code_expiration_minutes()),
        )
    )
    return code


async def send_password_reset_code_email(
    email: str,
    first_name: str,
    code: str,
) -> None:
    normalized_name = (first_name or "").strip() or "bonjour"
    safe_name = escape(normalized_name)
    safe_code = escape(code)
    expiration = reset_code_expiration_minutes()
    html = f"""
    <!doctype html>
    <html lang="fr">
      <body style="margin:0;background:#f8fafc;font-family:Arial,sans-serif;color:#0f172a">
        <div style="max-width:600px;margin:0 auto;padding:40px 20px">
          <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;padding:36px">
            <h1 style="margin:0 0 20px;font-size:28px">Réinitialisation du mot de passe</h1>
            <p>Bonjour {safe_name},</p>
            <p>Voici votre code temporaire pour choisir un nouveau mot de passe :</p>
            <p style="margin:28px 0;font-size:32px;font-weight:800;letter-spacing:8px;color:#2563eb">{safe_code}</p>
            <p style="font-size:14px;color:#64748b">Ce code expire dans {expiration} minutes et ne peut être utilisé qu'une seule fois.</p>
            <p style="font-size:14px;color:#64748b">Si vous n'avez pas demandé cette réinitialisation, ignorez cet e-mail. Votre mot de passe actuel reste inchangé.</p>
          </div>
        </div>
      </body>
    </html>
    """
    text = (
        f"Bonjour {normalized_name},\n\n"
        f"Votre code temporaire RuinionAI est : {code}\n\n"
        f"Il expire dans {expiration} minutes et ne peut être utilisé qu'une seule fois.\n"
        "Si vous n'avez pas fait cette demande, ignorez cet e-mail."
    )
    await send_email(
        email,
        "Votre code de réinitialisation RuinionAI",
        html,
        text=text,
    )


async def send_password_changed_email(email: str, first_name: str) -> None:
    normalized_name = (first_name or "").strip() or "bonjour"
    safe_name = escape(normalized_name)
    html = f"""
    <!doctype html>
    <html lang="fr">
      <body style="margin:0;background:#f8fafc;font-family:Arial,sans-serif;color:#0f172a">
        <div style="max-width:600px;margin:0 auto;padding:40px 20px">
          <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;padding:36px">
            <h1 style="margin:0 0 20px;font-size:28px">Mot de passe modifié</h1>
            <p>Bonjour {safe_name},</p>
            <p>Le mot de passe de votre compte RuinionAI vient d'être modifié.</p>
            <p style="font-size:14px;color:#64748b">Si vous n'êtes pas à l'origine de cette modification, contactez immédiatement le support.</p>
          </div>
        </div>
      </body>
    </html>
    """
    text = (
        f"Bonjour {normalized_name},\n\n"
        "Le mot de passe de votre compte RuinionAI vient d'être modifié.\n"
        "Si vous n'êtes pas à l'origine de cette modification, contactez le support."
    )
    await send_email(
        email,
        "Votre mot de passe RuinionAI a été modifié",
        html,
        text=text,
    )


async def deliver_password_reset_code_email(
    email: str,
    first_name: str,
    code: str,
) -> None:
    try:
        await send_password_reset_code_email(email, first_name, code)
    except Exception:
        logger.exception("Echec de l'envoi du code de réinitialisation.")


async def deliver_password_changed_email(email: str, first_name: str) -> None:
    try:
        await send_password_changed_email(email, first_name)
    except Exception:
        logger.exception("Echec de l'envoi de la confirmation de changement de mot de passe.")
