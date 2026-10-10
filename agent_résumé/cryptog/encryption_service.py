"""Chiffrement des données sensibles des réunions avec AES-256-GCM."""

import base64
import json
import os
import re
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


ENCRYPTED_PREFIX = "enc"

ENCRYPTED_MEETING_FIELDS = frozenset(
    {
        "transcription",
        "transcription_segments",
        "summary_short",
        "summary_long",
    }
)


class EncryptionConfigurationError(RuntimeError):
    """La configuration des clés de chiffrement est invalide."""


class DataDecryptionError(ValueError):
    """Une donnée chiffrée est invalide ou a été altérée."""


def _validate_key_id(key_id: str) -> str:
    key_id = (key_id or "").strip()

    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", key_id):
        raise EncryptionConfigurationError(
            "L’identifiant de clé de chiffrement est invalide."
        )

    return key_id


def _active_key_id() -> str:
    return _validate_key_id(
        os.getenv("MEETING_ENCRYPTION_ACTIVE_KEY_ID", "")
    )


def _read_key_value(key_id: str) -> str:
    """
    Charge une clé depuis une variable d’environnement ou un fichier secret.

    En local :
        MEETING_ENCRYPTION_KEY_V1=...

    En production :
        MEETING_ENCRYPTION_KEY_V1_FILE=/run/secrets/meeting_encryption_key_v1
    """
    suffix = re.sub(r"[^A-Za-z0-9]", "_", key_id).upper()

    value_name = f"MEETING_ENCRYPTION_KEY_{suffix}"
    file_name = f"{value_name}_FILE"

    direct_value = os.getenv(value_name, "").strip()
    secret_file = os.getenv(file_name, "").strip()

    if direct_value and secret_file:
        raise EncryptionConfigurationError(
            f"Configurez {value_name} ou {file_name}, mais pas les deux."
        )

    if direct_value:
        return direct_value

    if secret_file:
        path = Path(secret_file)

        try:
            return path.read_text(encoding="utf-8").strip()
        except OSError as error:
            raise EncryptionConfigurationError(
                "Le fichier contenant la clé de chiffrement est inaccessible."
            ) from error

    raise EncryptionConfigurationError(
        f"Configuration manquante : {value_name} ou {file_name}."
    )


def _load_key(key_id: str) -> bytes:
    key_id = _validate_key_id(key_id)
    encoded_key = _read_key_value(key_id)

    try:
        key = base64.b64decode(
            encoded_key.encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
    except (ValueError, UnicodeEncodeError) as error:
        raise EncryptionConfigurationError(
            "La clé de chiffrement doit être encodée en Base64."
        ) from error

    if len(key) != 32:
        raise EncryptionConfigurationError(
            "La clé de chiffrement AES-256 doit contenir exactement 32 octets."
        )

    return key


def _build_aad(
    organization_id: int,
    meeting_id: int,
    field_name: str,
) -> bytes:
    """
    Construit les données authentifiées par AES-GCM.

    L’AAD empêche de déplacer une valeur chiffrée vers une autre réunion,
    une autre organisation ou un autre champ.
    """
    if not isinstance(organization_id, int) or organization_id <= 0:
        raise ValueError("organization_id doit être un entier positif.")

    if not isinstance(meeting_id, int) or meeting_id <= 0:
        raise ValueError("meeting_id doit être un entier positif.")

    if field_name not in ENCRYPTED_MEETING_FIELDS:
        raise ValueError(
            f"Le champ {field_name!r} ne peut pas être chiffré par ce service."
        )

    return (
        f"ruinionai|organization={organization_id}"
        f"|meeting={meeting_id}|field={field_name}"
    ).encode("utf-8")


def is_encrypted(value: str | None) -> bool:
    return isinstance(value, str) and value.startswith(
        f"{ENCRYPTED_PREFIX}:"
    )


def encrypt_text(
    value: str | None,
    *,
    organization_id: int,
    meeting_id: int,
    field_name: str,
) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise TypeError("La valeur à chiffrer doit être une chaîne de caractères.")

    key_id = _active_key_id()
    key = _load_key(key_id)
    nonce = os.urandom(12)

    aad = _build_aad(
        organization_id,
        meeting_id,
        field_name,
    )

    ciphertext = AESGCM(key).encrypt(
        nonce,
        value.encode("utf-8"),
        aad,
    )

    payload = base64.urlsafe_b64encode(
        nonce + ciphertext
    ).decode("ascii")

    return f"{ENCRYPTED_PREFIX}:{key_id}:{payload}"


def decrypt_text(
    value: str | None,
    *,
    organization_id: int,
    meeting_id: int,
    field_name: str,
) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise DataDecryptionError(
            "La donnée chiffrée possède un format invalide."
        )

    try:
        prefix, key_id, encoded_payload = value.split(":", 2)
    except ValueError as error:
        raise DataDecryptionError(
            "La donnée n’est pas dans un format chiffré reconnu."
        ) from error

    if prefix != ENCRYPTED_PREFIX:
        raise DataDecryptionError(
            "La donnée n’est pas dans un format chiffré reconnu."
        )

    key = _load_key(key_id)

    try:
        payload = base64.b64decode(
            encoded_payload.encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
    except (ValueError, UnicodeEncodeError) as error:
        raise DataDecryptionError(
            "La donnée chiffrée est invalide."
        ) from error

    # 12 octets de nonce et au minimum 16 octets de tag GCM.
    if len(payload) < 28:
        raise DataDecryptionError(
            "La donnée chiffrée est incomplète."
        )

    nonce = payload[:12]
    ciphertext = payload[12:]

    aad = _build_aad(
        organization_id,
        meeting_id,
        field_name,
    )

    try:
        plaintext = AESGCM(key).decrypt(
            nonce,
            ciphertext,
            aad,
        )
        return plaintext.decode("utf-8")
    except (InvalidTag, UnicodeDecodeError) as error:
        raise DataDecryptionError(
            "La donnée ne peut pas être déchiffrée ou a été altérée."
        ) from error


def encrypt_json(
    value: Any,
    *,
    organization_id: int,
    meeting_id: int,
    field_name: str,
) -> str | None:
    if value is None:
        return None

    serialized = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return encrypt_text(
        serialized,
        organization_id=organization_id,
        meeting_id=meeting_id,
        field_name=field_name,
    )


def decrypt_json(
    value: str | None,
    *,
    organization_id: int,
    meeting_id: int,
    field_name: str,
) -> Any:
    plaintext = decrypt_text(
        value,
        organization_id=organization_id,
        meeting_id=meeting_id,
        field_name=field_name,
    )

    if plaintext is None:
        return None

    try:
        return json.loads(plaintext)
    except json.JSONDecodeError as error:
        raise DataDecryptionError(
            "Le contenu JSON déchiffré est invalide."
        ) from error