"""Chiffrement explicite des champs sensibles du modèle Meeting."""

from cryptog.encryption_service import (
    DataDecryptionError,
    decrypt_json,
    decrypt_text,
    encrypt_json,
    encrypt_text,
    is_encrypted,
)

TEXT_FIELDS = frozenset(
    {
        "transcription",
        "summary_short",
        "summary_long",
    }
)

JSON_FIELDS = frozenset(
    {
        "transcription_segments",
    }
)

SENSITIVE_MEETING_FIELDS = TEXT_FIELDS | JSON_FIELDS

def encrypt_meeting_values(
     *,
    organization_id: int,
    meeting_id: int,
    values: dict,
) -> dict:
    """
    Chiffre les champs sensibles présents dans un dictionnaire de mise à jour.

    Les autres valeurs, comme processing_status ou audio_duration,
    sont conservées sans modification.
    """
    encrypted_values = dict(values)
    
    for field_name in SENSITIVE_MEETING_FIELDS:
        if field_name not in encrypted_values:
            continue
        
        value = encrypted_values[field_name]
        
        if value is None:
            continue
        
        # Rend l’opération idempotente et évite un double chiffrement.
        if is_encrypted(value):
            continue
        
        if field_name in JSON_FIELDS:
            encrypted_values[field_name] = encrypt_json(
                value,
                organization_id=organization_id,
                meeting_id=meeting_id,
                field_name=field_name,
            )
        else:
            encrypted_values[field_name] = encrypt_text(
                value,
                organization_id=organization_id,
                meeting_id=meeting_id,
                field_name=field_name,
            )
            
    return encrypted_values


def decrypt_meeting_value(
    meeting, 
    field_name: str,
    *,
    allow_legacy_plaintext: bool = False,
):
    """
    Déchiffre explicitement un champ d’une réunion.

    allow_legacy_plaintext sera utilisé temporairement pendant la migration
    des anciennes données déjà présentes en clair.
    """
    if field_name not in SENSITIVE_MEETING_FIELDS:
        raise ValueError(
            f"Le champ {field_name!r} n’est pas un champ sensible de réunion."
        )

    organization_id = meeting.organization_id
    meeting_id = meeting.id

    if not organization_id or not meeting_id:
        raise DataDecryptionError(
            "La réunion doit être enregistrée avant le déchiffrement."
        )

    value = getattr(meeting, field_name)

    if value is None:
        return None

    if not is_encrypted(value):
        if allow_legacy_plaintext:
            return value

        raise DataDecryptionError(
            "Une donnée sensible est encore enregistrée en clair."
        )

    if field_name in JSON_FIELDS:
        return decrypt_json(
            value,
            organization_id=organization_id,
            meeting_id=meeting_id,
            field_name=field_name,
        )

    return decrypt_text(
        value,
        organization_id=organization_id,
        meeting_id=meeting_id,
        field_name=field_name,
    )
    
    
def decrypt_meeting_content(
    meeting,
    *,
    allow_legacy_plaintext: bool = False,
) -> dict:
    """Retourne tout le contenu privé déchiffré d’une réunion."""
    return {
        field_name: decrypt_meeting_value(
            meeting,
            field_name,
            allow_legacy_plaintext=allow_legacy_plaintext,
        )
        for field_name in SENSITIVE_MEETING_FIELDS
    }