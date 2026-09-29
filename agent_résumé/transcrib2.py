"""Compatibility entry point for the Mistral transcription service."""
from transcription_service import transcribe_audio_with_segments


def transcribe_audio(audio_bytes: bytes, file_name: str, content_type: str, language="fr") -> str:
    # The language is detected automatically when requesting segment timestamps.
    return transcribe_audio_with_segments(audio_bytes, file_name, content_type)["transcription"]
