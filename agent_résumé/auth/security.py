"""Primitives d'authentification centralisées et configuration validée."""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import bcrypt
import jwt
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
if len(SECRET_KEY) < 32:
    raise RuntimeError("SECRET_KEY doit contenir au moins 32 caractères")

# L'algorithme n'est volontairement pas configurable depuis l'environnement.
ALGORITHM = "HS256"
TOKEN_ISSUER = "ruinionai"
TOKEN_AUDIENCE = "ruinionai-api"


def _access_token_lifetime() -> int:
    raw_value = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30").strip()
    try:
        value = int(raw_value)
    except ValueError as error:
        raise RuntimeError(
            "ACCESS_TOKEN_EXPIRE_MINUTES doit être un entier."
        ) from error
    if not 5 <= value <= 60:
        raise RuntimeError(
            "ACCESS_TOKEN_EXPIRE_MINUTES doit être compris entre 5 et 60."
        )
    return value


ACCESS_TOKEN_EXPIRE_MINUTES = _access_token_lifetime()


def _password_bytes(password: str) -> bytes:
    if not isinstance(password, str):
        raise TypeError("Le mot de passe doit être une chaîne de caractères.")
    encoded = password.encode("utf-8")
    if len(encoded) > 72:
        raise ValueError("Le mot de passe ne peut pas dépasser 72 octets.")
    return encoded


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("ascii")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            _password_bytes(plain_password),
            password_hash.encode("ascii"),
        )
    except (TypeError, ValueError, UnicodeEncodeError):
        return False


def create_access_token(subject: str, token_version: int = 0) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "ver": int(token_version),
        "jti": uuid4().hex,
        "typ": "access",
        "iss": TOKEN_ISSUER,
        "aud": TOKEN_AUDIENCE,
        "iat": now,
        "exp": expires_at,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
        audience=TOKEN_AUDIENCE,
        issuer=TOKEN_ISSUER,
        options={
            "require": ["sub", "ver", "jti", "typ", "iat", "exp", "iss", "aud"],
        },
    )
