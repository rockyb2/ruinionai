import os
import unittest
from unittest.mock import Mock, patch

from transcription_orchestrator import (
    AllTranscriptionProvidersFailed,
    configured_transcription_providers,
    transcribe_with_fallback,
)


VALID_RESULT = {
    "transcription": "Bonjour",
    "transcription_segments": [
        {"start": 0.0, "end": 1.0, "text": "Bonjour"},
    ],
}


class ProviderError(RuntimeError):
    def __init__(self, status_code):
        self.status_code = status_code
        super().__init__(f"provider-{status_code}")


class TranscriptionOrchestratorTests(unittest.TestCase):
    def test_configuration_preserves_order_and_removes_duplicates(self):
        with patch.dict(os.environ, {
            "TRANSCRIPTION_PROVIDER_IDS": (
                "elevenlabs/scribe_v2, mistral/voxtral-mini-latest, "
                "elevenlabs/scribe_v2"
            ),
        }, clear=False):
            providers = configured_transcription_providers()

        self.assertEqual(
            [provider.identifier for provider in providers],
            ["elevenlabs/scribe_v2", "mistral/voxtral-mini-latest"],
        )

    def test_primary_success_does_not_call_fallback(self):
        primary = Mock(return_value=VALID_RESULT)
        fallback = Mock(return_value=VALID_RESULT)

        with patch.dict(os.environ, {
            "TRANSCRIPTION_PROVIDER_IDS": (
                "elevenlabs/scribe_v2,mistral/voxtral-mini-latest"
            ),
        }, clear=False):
            result = transcribe_with_fallback({
                "elevenlabs": primary,
                "mistral": fallback,
            })

        self.assertEqual(result, VALID_RESULT)
        primary.assert_called_once_with("scribe_v2")
        fallback.assert_not_called()

    def test_permanent_error_uses_fallback_without_retry(self):
        primary = Mock(side_effect=ProviderError(401))
        fallback = Mock(return_value=VALID_RESULT)

        with patch.dict(os.environ, {
            "TRANSCRIPTION_PROVIDER_IDS": (
                "elevenlabs/scribe_v2,mistral/voxtral-mini-latest"
            ),
        }, clear=False):
            result = transcribe_with_fallback({
                "elevenlabs": primary,
                "mistral": fallback,
            })

        self.assertEqual(result, VALID_RESULT)
        self.assertEqual(primary.call_count, 1)
        self.assertEqual(fallback.call_count, 1)

    def test_transient_error_is_retried_then_uses_fallback(self):
        primary = Mock(side_effect=ProviderError(429))
        fallback = Mock(return_value=VALID_RESULT)
        sleep = Mock()

        with patch.dict(os.environ, {
            "TRANSCRIPTION_PROVIDER_IDS": (
                "elevenlabs/scribe_v2,mistral/voxtral-mini-latest"
            ),
        }, clear=False):
            result = transcribe_with_fallback(
                {"elevenlabs": primary, "mistral": fallback},
                sleep_function=sleep,
            )

        self.assertEqual(result, VALID_RESULT)
        self.assertEqual(primary.call_count, 2)
        sleep.assert_called_once_with(5)
        fallback.assert_called_once_with("voxtral-mini-latest")

    def test_invalid_result_uses_next_provider(self):
        primary = Mock(return_value={
            "transcription": "",
            "transcription_segments": [],
        })
        fallback = Mock(return_value=VALID_RESULT)

        with patch.dict(os.environ, {
            "TRANSCRIPTION_PROVIDER_IDS": (
                "elevenlabs/scribe_v2,mistral/voxtral-mini-latest"
            ),
        }, clear=False):
            result = transcribe_with_fallback({
                "elevenlabs": primary,
                "mistral": fallback,
            })

        self.assertEqual(result, VALID_RESULT)
        self.assertEqual(primary.call_count, 1)
        self.assertEqual(fallback.call_count, 1)

    def test_all_failures_raise_one_safe_exception(self):
        with patch.dict(os.environ, {
            "TRANSCRIPTION_PROVIDER_IDS": (
                "elevenlabs/scribe_v2,mistral/voxtral-mini-latest"
            ),
        }, clear=False):
            with self.assertRaises(AllTranscriptionProvidersFailed) as raised:
                transcribe_with_fallback({
                    "elevenlabs": Mock(side_effect=ProviderError(401)),
                    "mistral": Mock(side_effect=ProviderError(403)),
                })

        self.assertEqual(len(raised.exception.failures), 2)
        self.assertNotIn("provider-", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
