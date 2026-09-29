"""Mistral transcription with validated timestamps for audio navigation."""
import math
import os

from mistralai.client import Mistral

MAX_CONSECUTIVE_REPEATS = 2


def _value(segment, name):
    return segment.get(name) if isinstance(segment, dict) else getattr(segment, name, None)


def clean_transcription_segments(raw_segments, expected_duration=None, offset=0.0):
    """Discard impossible timestamps and stop provider repetition loops."""
    cleaned = []
    previous = None
    repeat_count = 0
    duration = float(expected_duration) if expected_duration else None
    for segment in raw_segments or []:
        try:
            start = float(_value(segment, "start"))
            end = float(_value(segment, "end"))
        except (TypeError, ValueError):
            continue
        text = " ".join(str(_value(segment, "text") or "").split())
        if not text or not math.isfinite(start) or not math.isfinite(end) or start < 0 or end <= start:
            continue
        if duration is not None and start > duration + 1:
            continue
        if duration is not None:
            end = min(end, duration)
            if end <= start:
                continue
        normalized = text.casefold()
        if normalized == previous:
            repeat_count += 1
            if repeat_count >= MAX_CONSECUTIVE_REPEATS:
                continue
        else:
            previous = normalized
            repeat_count = 0
        cleaned.append({"start": start + offset, "end": end + offset, "text": text})
    cleaned.sort(key=lambda item: item["start"])
    return cleaned


def transcribe_audio_with_segments(audio_bytes: bytes, file_name: str, content_type: str,
                                   expected_duration=None, timestamp_offset=0.0) -> dict:
    api_key = os.getenv("MISTRAL_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Configuration manquante : MISTRAL_API_KEY.")
    if not audio_bytes:
        raise ValueError("La note vocale est vide.")
    client = Mistral(api_key=api_key)
    response = client.audio.transcriptions.complete(
        model=os.getenv("MISTRAL_AUDIO_MODEL", "voxtral-mini-latest"),
        file={"content": audio_bytes, "file_name": file_name or "note-vocale.mp3",
              "content_type": content_type or "audio/mpeg"},
        timestamp_granularities=["segment"], retries=None, timeout_ms=85000,
    )
    segments = clean_transcription_segments(
        getattr(response, "segments", None), expected_duration, timestamp_offset,
    )
    # The provider's global text can contain a hallucinated repetition loop.
    # Validated timestamped segments are the source of truth.
    text = " ".join(segment["text"] for segment in segments).strip()
    if not text:
        raise ValueError("La transcription est vide. Vérifiez que l’audio contient des voix audibles.")
    return {"transcription": text, "transcription_segments": segments}
