import base64
import os
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from meeting_crypto import (
    decrypt_meeting_content,
    decrypt_meeting_value,
    encrypt_meeting_values,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from cryptog.encryption_service import (
    DataDecryptionError,
    EncryptionConfigurationError,
    decrypt_json,
    decrypt_text,
    encrypt_json,
    encrypt_text,
    is_encrypted,
)


TEST_KEY = base64.urlsafe_b64encode(
    AESGCM.generate_key(bit_length=256)
).decode("ascii")


class EncryptionServiceTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(
            os.environ,
            {
                "MEETING_ENCRYPTION_ACTIVE_KEY_ID": "v1",
                "MEETING_ENCRYPTION_KEY_V1": TEST_KEY,
            },
            clear=True,
        )
        self.environment.start()

    def tearDown(self):
        self.environment.stop()

    def test_text_can_be_encrypted_and_decrypted(self):
        plaintext = "Décision confidentielle de la réunion."

        encrypted = encrypt_text(
            plaintext,
            organization_id=12,
            meeting_id=48,
            field_name="transcription",
        )

        self.assertTrue(is_encrypted(encrypted))
        self.assertNotIn(plaintext, encrypted)
        self.assertTrue(encrypted.startswith("enc:v1:"))

        decrypted = decrypt_text(
            encrypted,
            organization_id=12,
            meeting_id=48,
            field_name="transcription",
        )

        self.assertEqual(decrypted, plaintext)

    def test_each_encryption_uses_a_different_nonce(self):
        arguments = {
            "organization_id": 12,
            "meeting_id": 48,
            "field_name": "summary_short",
        }

        first = encrypt_text("Même contenu", **arguments)
        second = encrypt_text("Même contenu", **arguments)

        self.assertNotEqual(first, second)
        self.assertEqual(decrypt_text(first, **arguments), "Même contenu")
        self.assertEqual(decrypt_text(second, **arguments), "Même contenu")

    def test_modified_ciphertext_is_rejected(self):
        encrypted = encrypt_text(
            "Information privée",
            organization_id=12,
            meeting_id=48,
            field_name="summary_long",
        )

        prefix, key_id, encoded_payload = encrypted.split(":", 2)
        payload = bytearray(
            base64.urlsafe_b64decode(encoded_payload.encode("ascii"))
        )

        payload[-1] ^= 1

        altered = (
            f"{prefix}:{key_id}:"
            + base64.urlsafe_b64encode(payload).decode("ascii")
        )

        with self.assertRaises(DataDecryptionError):
            decrypt_text(
                altered,
                organization_id=12,
                meeting_id=48,
                field_name="summary_long",
            )

    def test_ciphertext_cannot_be_moved_to_another_meeting(self):
        encrypted = encrypt_text(
            "Réunion numéro 48",
            organization_id=12,
            meeting_id=48,
            field_name="transcription",
        )

        with self.assertRaises(DataDecryptionError):
            decrypt_text(
                encrypted,
                organization_id=12,
                meeting_id=49,
                field_name="transcription",
            )

    def test_ciphertext_cannot_be_moved_to_another_field(self):
        encrypted = encrypt_text(
            "Résumé court",
            organization_id=12,
            meeting_id=48,
            field_name="summary_short",
        )

        with self.assertRaises(DataDecryptionError):
            decrypt_text(
                encrypted,
                organization_id=12,
                meeting_id=48,
                field_name="summary_long",
            )

    def test_json_segments_can_be_encrypted_and_decrypted(self):
        segments = [
            {
                "start": 0.0,
                "end": 2.5,
                "text": "Bonjour à tous.",
            },
            {
                "start": 2.5,
                "end": 5.0,
                "text": "La réunion commence.",
            },
        ]

        encrypted = encrypt_json(
            segments,
            organization_id=12,
            meeting_id=48,
            field_name="transcription_segments",
        )

        self.assertTrue(is_encrypted(encrypted))
        self.assertNotIn("Bonjour à tous", encrypted)

        decrypted = decrypt_json(
            encrypted,
            organization_id=12,
            meeting_id=48,
            field_name="transcription_segments",
        )

        self.assertEqual(decrypted, segments)

    def test_plaintext_is_rejected_by_decryption(self):
        with self.assertRaises(DataDecryptionError):
            decrypt_text(
                "Texte encore en clair",
                organization_id=12,
                meeting_id=48,
                field_name="transcription",
            )

    def test_invalid_key_length_is_rejected(self):
        invalid_key = base64.urlsafe_b64encode(
            b"cle-trop-courte"
        ).decode("ascii")

        with patch.dict(
            os.environ,
            {"MEETING_ENCRYPTION_KEY_V1": invalid_key},
        ):
            with self.assertRaises(EncryptionConfigurationError):
                encrypt_text(
                    "Contenu",
                    organization_id=12,
                    meeting_id=48,
                    field_name="transcription",
                )
    def test_meeting_values_are_encrypted_before_database_storage(self):
        values = {
            "transcription": "Discussion privée",
            "transcription_segments": [
                {
                    "start": 0.0,
                    "end": 2.0,
                    "text": "Discussion privée",
                }
            ],
            "summary_short": "Résumé privé",
            "summary_long": "Compte rendu privé",
            "processing_status": "writing",
        }

        encrypted = encrypt_meeting_values(
            organization_id=12,
            meeting_id=48,
            values=values,
        )

        self.assertTrue(is_encrypted(encrypted["transcription"]))
        self.assertTrue(is_encrypted(encrypted["transcription_segments"]))
        self.assertTrue(is_encrypted(encrypted["summary_short"]))
        self.assertTrue(is_encrypted(encrypted["summary_long"]))

        # Les champs non sensibles ne doivent pas être modifiés.
        self.assertEqual(encrypted["processing_status"], "writing")

        serialized = str(encrypted)
        self.assertNotIn("Discussion privée", serialized)
        self.assertNotIn("Résumé privé", serialized)
        self.assertNotIn("Compte rendu privé", serialized)


    def test_meeting_content_requires_explicit_decryption(self):
        encrypted = encrypt_meeting_values(
            organization_id=12,
            meeting_id=48,
            values={
                "transcription": "Discussion privée",
                "transcription_segments": [
                    {
                        "start": 0.0,
                        "end": 2.0,
                        "text": "Discussion privée",
                    }
                ],
                "summary_short": "Résumé privé",
                "summary_long": "Compte rendu privé",
            },
        )

        meeting = SimpleNamespace(
            id=48,
            organization_id=12,
            **encrypted,
        )

        content = decrypt_meeting_content(meeting)

        self.assertEqual(content["transcription"], "Discussion privée")
        self.assertEqual(content["summary_short"], "Résumé privé")
        self.assertEqual(content["summary_long"], "Compte rendu privé")
        self.assertEqual(
            content["transcription_segments"][0]["text"],
            "Discussion privée",
        )


    def test_legacy_plaintext_requires_explicit_permission(self):
        meeting = SimpleNamespace(
            id=48,
            organization_id=12,
            transcription="Ancienne transcription en clair",
        )

        with self.assertRaises(DataDecryptionError):
            decrypt_meeting_value(
                meeting,
                "transcription",
            )

        value = decrypt_meeting_value(
            meeting,
            "transcription",
            allow_legacy_plaintext=True,
        )

        self.assertEqual(value, "Ancienne transcription en clair")
                
        


if __name__ == "__main__":
    unittest.main()