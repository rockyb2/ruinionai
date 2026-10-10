"""Mistral transcription with validated timestamps for audio navigation."""
import math
import os

from mistralai.client import Mistral
from observability import sanitized_observation

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
    
    from langfuse import get_client

    client = Mistral(api_key=api_key)
    langfuse = get_client()

    model = os.getenv(
        "MISTRAL_AUDIO_MODEL",
        "voxtral-mini-latest",
    )

    with sanitized_observation(
        langfuse.start_as_current_observation(
            as_type="generation",
            name="transcription-audio",
            model=model,
            input={
                "audio_size_bytes": len(audio_bytes),
                "expected_duration_seconds": expected_duration,
            },
            model_parameters={
                "timestamp_granularity": "segment",
                "timeout_ms": 85000,
            },
            metadata={
                "provider": "mistral",
                "feature": "audio-transcription",
            },
        ),
        "La transcription audio a échoué.",
    ) as generation:
        response = client.audio.transcriptions.complete(
            model=model,
            file={
                "content": audio_bytes,
                "file_name": file_name or "note-vocale.mp3",
                "content_type": content_type or "audio/mpeg",
            },
            timestamp_granularities=["segment"],
            retries=None,
            timeout_ms=85000,
        )

        raw_segments = getattr(response, "segments", None) or []

        segments = clean_transcription_segments(
            raw_segments,
            expected_duration,
            timestamp_offset,
        )

        text = " ".join(
            segment["text"] for segment in segments
        ).strip()

        if not text:
            raise ValueError(
                "La transcription est vide. "
                "Vérifiez que l’audio contient des voix audibles."
            )

        # La durée facturée correspond normalement à la durée transmise.
        billed_seconds = float(expected_duration or 0)

        # Pour les appels anciens qui ne transmettent pas la durée,
        # on la déduit des horodatages du fournisseur.
        if billed_seconds <= 0 and raw_segments:
            valid_ends = []

            for segment in raw_segments:
                try:
                    end = float(
                        segment.get("end")
                        if isinstance(segment, dict)
                        else getattr(segment, "end", 0)
                    )

                    if math.isfinite(end) and end > 0:
                        valid_ends.append(end)

                except (TypeError, ValueError):
                    continue

            if valid_ends:
                billed_seconds = max(valid_ends)

        generation.update(
            output={
                "status": "completed",
                "transcription_characters": len(text),
                "segment_count": len(segments),
            },
            usage_details={
                # Arrondi supérieur afin de ne pas sous-estimer la durée facturée.
                "seconds": math.ceil(billed_seconds),
            },
            metadata={
                "provider": "mistral",
                "feature": "audio-transcription",
                "raw_segment_count": len(raw_segments),
                "clean_segment_count": len(segments),
            },
        )

        return {
            "transcription": text,
            "transcription_segments": segments,
        }
    
            
        
                    
            

    
    
    # ancien code ce n'est pas pro mais c'est mon app 👍
    # response = client.audio.transcriptions.complete(
    #     model=os.getenv("MISTRAL_AUDIO_MODEL", "voxtral-mini-latest"),
    #     file={"content": audio_bytes, "file_name": file_name or "note-vocale.mp3",
    #           "content_type": content_type or "audio/mpeg"},
    #     timestamp_granularities=["segment"], retries=None, timeout_ms=85000,
    # )
    # segments = clean_transcription_segments(
    #     getattr(response, "segments", None), expected_duration, timestamp_offset,
    # )
    # # The provider's global text can contain a hallucinated repetition loop.
    # # Validated timestamped segments are the source of truth.
    # text = " ".join(segment["text"] for segment in segments).strip()
    # if not text:
    #     raise ValueError("La transcription est vide. Vérifiez que l’audio contient des voix audibles.")
    # return {"transcription": text, "transcription_segments": segments}
