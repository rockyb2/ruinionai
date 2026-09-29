"""Validate transcription without sending recordings to an external provider."""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from transcrib2 import transcribe_audio
from transcription_service import clean_transcription_segments, transcribe_audio_with_segments


class MistralTranscriptionTests(unittest.TestCase):
    @patch.dict(os.environ, {"MISTRAL_API_KEY": "test-only-key", "MISTRAL_AUDIO_MODEL": "test-model"})
    @patch("transcription_service.Mistral")
    def test_audio_timestamps_no_language_conflict_and_no_hidden_retries(self, client_class):
        client_class.return_value.audio.transcriptions.complete.return_value = SimpleNamespace(
            text=" Bonjour à tous. ",
            segments=[SimpleNamespace(start=1.5, end=2.5, text=" Bonjour à tous. "),
                      SimpleNamespace(start=-1, end=0, text="invalid")],
        )
        result = transcribe_audio_with_segments(b"short audio", "test.mp3", "audio/mpeg")
        self.assertEqual(result["transcription"], "Bonjour à tous.")
        self.assertEqual(result["transcription_segments"], [{"start": 1.5, "end": 2.5, "text": "Bonjour à tous."}])
        call = client_class.return_value.audio.transcriptions.complete.call_args.kwargs
        self.assertEqual(call["model"], "test-model")
        self.assertEqual(call["timestamp_granularities"], ["segment"])
        self.assertNotIn("language", call)
        self.assertIsNone(call["retries"])
        self.assertEqual(call["timeout_ms"], 85000)
        self.assertEqual(call["file"]["content"], b"short audio")
        self.assertEqual(transcribe_audio(b"short audio", "test.mp3", "audio/mpeg"), "Bonjour à tous.")

    @patch.dict(os.environ, {"MISTRAL_API_KEY": ""})
    def test_missing_api_key_is_reported_before_network_call(self):
        with self.assertRaisesRegex(ValueError, "MISTRAL_API_KEY"):
            transcribe_audio(b"short audio", "test.mp3", "audio/mpeg")

    @patch.dict(os.environ, {"MISTRAL_API_KEY": "test-only-key"})
    def test_empty_audio_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "vide"):
            transcribe_audio(b"", "test.mp3", "audio/mpeg")

    @patch.dict(os.environ, {"MISTRAL_API_KEY": "test-only-key"})
    @patch("transcription_service.Mistral")
    def test_empty_provider_response_is_rejected(self, client_class):
        client_class.return_value.audio.transcriptions.complete.return_value = SimpleNamespace(text=" ", segments=[])
        with self.assertRaisesRegex(ValueError, "vide"):
            transcribe_audio_with_segments(b"audio", "test.mp3", "audio/mpeg")

    def test_pathological_repetitions_and_late_segments_are_removed(self):
        segments = [
            {"start": 0, "end": 1, "text": "Une décision"},
            {"start": 1, "end": 2, "text": " Une   décision "},
            {"start": 2, "end": 3, "text": "une décision"},
            {"start": 3, "end": 4, "text": "Une décision"},
            {"start": 61, "end": 62, "text": "Après la fin"},
        ]
        cleaned = clean_transcription_segments(segments, expected_duration=60)
        self.assertEqual(len(cleaned), 2)
        self.assertEqual([item["text"] for item in cleaned], ["Une décision", "Une décision"])

    @patch.dict(os.environ, {"MISTRAL_API_KEY": "test-only-key"})
    @patch("transcription_service.Mistral")
    def test_validated_segments_replace_untrusted_provider_text(self, client_class):
        client_class.return_value.audio.transcriptions.complete.return_value = SimpleNamespace(
            text="hallucination " * 1000,
            segments=[SimpleNamespace(start=0, end=1, text="Texte réel")],
        )
        result = transcribe_audio_with_segments(b"audio", "test.mp3", "audio/mpeg", expected_duration=10)
        self.assertEqual(result["transcription"], "Texte réel")


if __name__ == "__main__":
    unittest.main()
