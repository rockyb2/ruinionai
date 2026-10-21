"""Adaptateur de transcription ElevenLabs Scribe v2."""

import math
import os
from io import BytesIO

from elevenlabs.client import ElevenLabs
from observability import sanitized_observation

MAX_SEGMENT_SECONDS = 15.0
MAX_SEGMENT_CHARACTERS = 240


def _value(item, name):
    """Lit une propriété sur un objet du SDK ou un dictionnaire."""
    if isinstance(item, dict):
        return item.get(name)

    return getattr(item, name, None)


def _append_word(current_text: str, word: str) -> str:
    """Reconstruit une phrase sans ajouter d’espace avant la ponctuation."""
    word = " ".join(str(word or "").split())

    if not word:
        return current_text

    if not current_text:
        return word

    if word[0] in ",.;:!?…)]}":
        return current_text + word

    if current_text.endswith(("'", "’", "-", "(", "[", "{")):
        return current_text + word

    return current_text + " " + word


def normalize_elevenlabs_words(
    raw_words,
    expected_duration=None,
    timestamp_offset=0.0,
):
    """
    Transforme les mots ElevenLabs en segments utilisables par Ruinion AI.

    Les identifiants speaker_0, speaker_1, etc. deviennent :
    Intervenant 1, Intervenant 2, etc.
    """
    duration = float(expected_duration) if expected_duration is not None else None

    speaker_labels = {}
    segments = []

    current_speaker = None
    current_start = None
    current_end = None
    current_text = ""

    def flush_segment():
        nonlocal current_speaker
        nonlocal current_start
        nonlocal current_end
        nonlocal current_text

        text = current_text.strip()

        if (
            text
            and current_speaker
            and current_start is not None
            and current_end is not None
            and current_end > current_start
        ):
            segments.append(
                {
                    "start": current_start + timestamp_offset,
                    "end": current_end + timestamp_offset,
                    "text": text,
                    "speaker": current_speaker,
                }
            )

        current_speaker = None
        current_start = None
        current_end = None
        current_text = ""

    for raw_word in raw_words or []:
        word_type = str(_value(raw_word, "type") or "word")

        # Les espaces sont reconstruits par _append_word.
        # Les événements audio sont ignorés pour le moment.
        if word_type != "word":
            continue

        text = str(_value(raw_word, "text") or "").strip()

        try:
            start = float(_value(raw_word, "start"))
            end = float(_value(raw_word, "end"))
        except (TypeError, ValueError):
            continue

        if (
            not text
            or not math.isfinite(start)
            or not math.isfinite(end)
            or start < 0
            or end <= start
        ):
            continue

        if duration is not None:
            if start > duration + 1:
                continue

            end = min(end, duration)

            if end <= start:
                continue

        speaker_id = str(_value(raw_word, "speaker_id") or "speaker_unknown")

        if speaker_id not in speaker_labels:
            speaker_labels[speaker_id] = f"Intervenant {len(speaker_labels) + 1}"

        speaker = speaker_labels[speaker_id]

        speaker_changed = current_speaker is not None and speaker != current_speaker

        segment_too_long = (
            current_start is not None and start - current_start >= MAX_SEGMENT_SECONDS
        )

        segment_too_large = len(current_text) + len(text) >= MAX_SEGMENT_CHARACTERS

        if speaker_changed or segment_too_long or segment_too_large:
            flush_segment()

        if current_start is None:
            current_start = start
            current_speaker = speaker

        current_end = end
        current_text = _append_word(current_text, text)

        # Une phrase terminée et suffisamment longue forme un segment.
        if (
            current_text.endswith((".", "!", "?", "…"))
            and current_end - current_start >= 4
        ):
            flush_segment()

    flush_segment()

    return segments


def build_speaker_transcription(segments):
    """
    Produit le texte complet en regroupant les segments consécutifs
    appartenant au même intervenant.
    """
    paragraphs = []

    for segment in segments:
        speaker = segment["speaker"]
        text = segment["text"]

        if paragraphs and paragraphs[-1]["speaker"] == speaker:
            paragraphs[-1]["text"] = _append_word(
                paragraphs[-1]["text"],
                text,
            )
        else:
            paragraphs.append(
                {
                    "speaker": speaker,
                    "text": text,
                }
            )

    return "\n\n".join(
        f'{paragraph["speaker"]} : {paragraph["text"]}' for paragraph in paragraphs
    )


def transcribe_with_elevenlabs(
    audio_bytes: bytes,
    file_name: str,
    content_type: str,
    expected_duration=None,
    timestamp_offset=0.0,
    model_id=None,
):
    """Transcrit un audio avec ElevenLabs Scribe v2."""
    api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()

    if not api_key:
        raise ValueError("Configuration manquante : ELEVENLABS_API_KEY.")

    if not audio_bytes:
        raise ValueError("La note vocale est vide.")


    model = (model_id or os.getenv("ELEVENLABS_AUDIO_MODEL", "scribe_v2")).strip()

    if not model:
        raise ValueError("Configuration manquante : ELEVENLABS_AUDIO_MODEL.")

    language = (
        os.getenv(
            "TRANSCRIPTION_LANGUAGE",
            "fra",
        ).strip()
        or None
    )

    audio_file = BytesIO(audio_bytes)
    audio_file.name = file_name or "enregistrement.mp3"

    from langfuse import get_client

    client = ElevenLabs(
        api_key=api_key,
        timeout=600,
    )
    langfuse = get_client()

    with sanitized_observation(
        langfuse.start_as_current_observation(
            as_type="generation",
            name="transcription-audio-elevenlabs",
            model=model,
            input={
                "audio_size_bytes": len(audio_bytes),
                "expected_duration_seconds": expected_duration,
            },
            model_parameters={
                "timestamps_granularity": "word",
                "diarization": True,
            },
            metadata={
                "provider": "elevenlabs",
                "feature": "audio-transcription",
            },
        ),
        "La transcription audio a échoué.",
    ) as generation:
        response = client.speech_to_text.convert(
            file=audio_file,
            model_id=model,
            language_code=language,
            timestamps_granularity="word",
            diarize=True,
            tag_audio_events=False,
        )

        segments = normalize_elevenlabs_words(
            getattr(response, "words", None),
            expected_duration=expected_duration,
            timestamp_offset=timestamp_offset,
        )

        if not segments:
            raise ValueError("ElevenLabs a retourné une transcription vide.")

        transcription = build_speaker_transcription(segments)
        speaker_count = len({segment["speaker"] for segment in segments})
        billed_seconds = max(0, math.ceil(float(expected_duration or 0)))

        generation.update(
            output={
                "status": "completed",
                "transcription_characters": len(transcription),
                "segment_count": len(segments),
                "speaker_count": speaker_count,
            },
            usage_details={"seconds": billed_seconds},
            metadata={
                "provider": "elevenlabs",
                "feature": "audio-transcription",
                "status": "completed",
                "diarization": True,
            },
        )

        return {
            "transcription": transcription,
            "transcription_segments": segments,
        }
