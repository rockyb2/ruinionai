"""Validate the Scribe v2 call without sending audio to ElevenLabs."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from transcrib2 import transcribe_audio


class ScribeTranscriptionTests(unittest.TestCase):
    @patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test-only-key"})
    @patch("transcrib2.ElevenLabs")
    def test_audio_is_sent_to_scribe_v2_in_french(self, client_class):
        client_class.return_value.speech_to_text.convert.return_value = SimpleNamespace(
            text=" Bonjour à tous. "
        )

        result = transcribe_audio(b"short audio", "test.mp3", "audio/mpeg", language="fr")

        self.assertEqual(result, "Bonjour à tous.")
        client_class.assert_called_once_with(api_key="test-only-key")
        call = client_class.return_value.speech_to_text.convert.call_args.kwargs
        self.assertEqual(call["model_id"], "scribe_v2")
        self.assertEqual(call["language_code"], "fr")
        self.assertEqual(call["file"].name, "test.mp3")
        self.assertEqual(call["file"].getvalue(), b"short audio")

    @patch.dict(os.environ, {"ELEVENLABS_API_KEY": ""})
    def test_missing_api_key_is_reported(self):
        with self.assertRaisesRegex(RuntimeError, "ELEVENLABS_API_KEY"):
            transcribe_audio(b"short audio", "test.mp3", "audio/mpeg")

    @patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test-only-key"})
    def test_empty_audio_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "vide"):
            transcribe_audio(b"", "test.mp3", "audio/mpeg")


if __name__ == "__main__":
    unittest.main()
