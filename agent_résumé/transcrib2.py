import os
from io import BytesIO

from elevenlabs.client import ElevenLabs


def transcribe_audio(
    audio_bytes: bytes,
    file_name: str,
    content_type: str,
    language: str = "fr",
) -> str:
    api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY est manquant.")

    if not audio_bytes:
        raise ValueError("La note vocale est vide.")

    audio_file = BytesIO(audio_bytes)
    audio_file.name = file_name or "note-vocale.mp3"

    client = ElevenLabs(api_key=api_key)
    response = client.speech_to_text.convert(
        file=audio_file,
        model_id="scribe_v2",
        language_code=language,
        tag_audio_events=False,
    )

    text = (getattr(response, "text", None) or "").strip()
    if not text:
        raise RuntimeError("La transcription a échoué.")

    return text