"""Tests de l'adaptateur ElevenLabs sans appel réseau."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from elevenlabs_transcription import (
    build_speaker_transcription,
    normalize_elevenlabs_words,
    transcribe_with_elevenlabs,
)


def word(text, start, end, speaker):
    return SimpleNamespace(
        type="word",
        text=text,
        start=start,
        end=end,
        speaker_id=speaker,
    )


class ElevenLabsTranscriptionTests(unittest.TestCase):
    def test_words_are_grouped_by_speaker(self):
        raw_words = [
            word("Bonjour", 0.0, 0.4, "speaker_0"),
            word("à", 0.4, 0.6, "speaker_0"),
            word("tous.", 0.6, 1.2, "speaker_0"),
            word("Bonjour", 1.3, 1.7, "speaker_1"),
            word("Jonathan.", 1.7, 2.2, "speaker_1"),
        ]

        segments = normalize_elevenlabs_words(
            raw_words,
            expected_duration=10,
        )

        self.assertEqual(len(segments), 2)
        self.assertEqual(
            segments[0],
            {
                "start": 0.0,
                "end": 1.2,
                "text": "Bonjour à tous.",
                "speaker": "Intervenant 1",
            },
        )
        self.assertEqual(
            segments[1],
            {
                "start": 1.3,
                "end": 2.2,
                "text": "Bonjour Jonathan.",
                "speaker": "Intervenant 2",
            },
        )

    def test_timestamp_offset_is_applied(self):
        raw_words = [
            word("Deuxième", 0.0, 0.5, "speaker_0"),
            word("partie.", 0.5, 1.0, "speaker_0"),
        ]

        segments = normalize_elevenlabs_words(
            raw_words,
            expected_duration=10,
            timestamp_offset=600,
        )

        self.assertEqual(segments[0]["start"], 600.0)
        self.assertEqual(segments[0]["end"], 601.0)

    def test_full_transcription_contains_speaker_names(self):
        segments = [
            {
                "start": 0.0,
                "end": 1.0,
                "text": "Premier message.",
                "speaker": "Intervenant 1",
            },
            {
                "start": 1.0,
                "end": 2.0,
                "text": "Suite du message.",
                "speaker": "Intervenant 1",
            },
            {
                "start": 2.0,
                "end": 3.0,
                "text": "Réponse.",
                "speaker": "Intervenant 2",
            },
        ]

        transcription = build_speaker_transcription(segments)

        self.assertEqual(
            transcription,
            (
                "Intervenant 1 : Premier message. Suite du message."
                "\n\n"
                "Intervenant 2 : Réponse."
            ),
        )

    @patch.dict(
        os.environ,
        {
            "ELEVENLABS_API_KEY": "test-only-key",
            "ELEVENLABS_AUDIO_MODEL": "scribe_v2",
            "TRANSCRIPTION_LANGUAGE": "fra",
        },
    )
    @patch("elevenlabs_transcription.ElevenLabs")
    def test_provider_is_called_with_diarization(self, client_class):
        client_class.return_value.speech_to_text.convert.return_value = (
            SimpleNamespace(
                words=[
                    word("Bonjour", 0.0, 0.5, "speaker_0"),
                    word("Awa.", 0.5, 1.0, "speaker_0"),
                ]
            )
        )

        result = transcribe_with_elevenlabs(
            b"audio-test",
            "reunion.mp3",
            "audio/mpeg",
            expected_duration=10,
        )

        self.assertEqual(
            result["transcription"],
            "Intervenant 1 : Bonjour Awa.",
        )
        self.assertEqual(
            result["transcription_segments"][0]["speaker"],
            "Intervenant 1",
        )

        client_class.assert_called_once_with(
            api_key="test-only-key",
            timeout=600,
        )

        call = (
            client_class.return_value
            .speech_to_text.convert.call_args.kwargs
        )

        self.assertEqual(call["model_id"], "scribe_v2")
        self.assertEqual(call["language_code"], "fra")
        self.assertEqual(call["timestamps_granularity"], "word")
        self.assertTrue(call["diarize"])
        self.assertFalse(call["tag_audio_events"])

        uploaded_file = call["file"]
        uploaded_file.seek(0)

        self.assertEqual(uploaded_file.read(), b"audio-test")
        self.assertEqual(uploaded_file.name, "reunion.mp3")

    @patch.dict(os.environ, {"ELEVENLABS_API_KEY": ""})
    def test_missing_api_key_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "ELEVENLABS_API_KEY",
        ):
            transcribe_with_elevenlabs(
                b"audio",
                "reunion.mp3",
                "audio/mpeg",
            )

    @patch.dict(
        os.environ,
        {"ELEVENLABS_API_KEY": "test-only-key"},
    )
    @patch("elevenlabs_transcription.ElevenLabs")
    def test_empty_response_is_rejected(self, client_class):
        client_class.return_value.speech_to_text.convert.return_value = (
            SimpleNamespace(words=[])
        )

        with self.assertRaisesRegex(
            ValueError,
            "transcription vide",
        ):
            transcribe_with_elevenlabs(
                b"audio",
                "reunion.mp3",
                "audio/mpeg",
            )

    @patch.dict(
        os.environ,
        {
            "ELEVENLABS_API_KEY": "test-only-key",
            "ELEVENLABS_AUDIO_MODEL": "scribe_v2",
        },
    )
    @patch("elevenlabs_transcription.ElevenLabs")
    @patch("langfuse.get_client")
    def test_langfuse_receives_cost_usage_without_private_content(
        self,
        get_client,
        client_class,
    ):
        client_class.return_value.speech_to_text.convert.return_value = (
            SimpleNamespace(words=[
                word("Projet", 0.0, 0.5, "speaker_0"),
                word("confidentiel.", 0.5, 1.0, "speaker_0"),
            ])
        )
        generation = MagicMock()
        observation_context = MagicMock()
        observation_context.__enter__.return_value = generation
        get_client.return_value.start_as_current_observation.return_value = (
            observation_context
        )

        transcribe_with_elevenlabs(
            b"audio-secret",
            "reunion-secrete.mp3",
            "audio/mpeg",
            expected_duration=61.2,
        )

        start = (
            get_client.return_value
            .start_as_current_observation.call_args.kwargs
        )
        update = generation.update.call_args.kwargs
        serialized = str({"start": start, "update": update})

        self.assertEqual(start["model"], "scribe_v2")
        self.assertEqual(update["usage_details"], {"seconds": 62})
        self.assertNotIn("Projet confidentiel", serialized)
        self.assertNotIn("reunion-secrete.mp3", serialized)
        self.assertNotIn("audio-secret", serialized)


if __name__ == "__main__":
    unittest.main()
