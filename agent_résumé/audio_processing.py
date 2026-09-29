"""Join independently finalized browser recordings without dropping later segments."""

import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic

MAX_AUDIO_BYTES = 500 * 1024 * 1024
MAX_AUDIO_SEGMENTS = 100
MAX_AUDIO_SECONDS = 4 * 60 * 60
PCM_BYTES_PER_SECOND = 16000 * 2  # Mono, 16-bit, 16 kHz.

# Force a known demuxer rather than interpreting arbitrary uploaded playlists.
INPUT_FORMATS = {
    "audio/webm": "matroska",
    "video/webm": "matroska",
    "audio/mp4": "mov",
    "video/mp4": "mov",
    "audio/x-m4a": "mov",
    "audio/ogg": "ogg",
    "application/ogg": "ogg",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/flac": "flac",
    "audio/x-flac": "flac",
    "audio/aac": "aac",
}


class AudioValidationError(ValueError):
    pass


def audio_input_format(content_type: str | None) -> str:
    media_type = (content_type or "").split(";")[0].strip().lower()
    if media_type not in INPUT_FORMATS:
        raise AudioValidationError("Format d’enregistrement non pris en charge. Utilisez WebM, M4A, OGG, WAV ou MP3.")
    return INPUT_FORMATS[media_type]


def merge_audio_segments(parts: list[tuple[Path, str]]) -> bytes:
    if not parts or len(parts) > MAX_AUDIO_SEGMENTS:
        raise AudioValidationError("Un enregistrement doit contenir entre 1 et 100 parties.")
    if sum(path.stat().st_size for path, _ in parts) > MAX_AUDIO_BYTES:
        raise AudioValidationError("La taille totale de l’audio dépasse 500 Mo.")

    executable = shutil.which("ffmpeg")
    if not executable:
        raise RuntimeError("FFmpeg est requis sur le serveur pour assembler les enregistrements.")

    deadline = monotonic() + 300

    def convert(arguments: list[str]):
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise AudioValidationError("L’assemblage audio a dépassé le délai autorisé.")
        try:
            result = subprocess.run(
                [executable, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", *arguments],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=min(120, remaining),
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AudioValidationError("L’assemblage audio a dépassé le délai autorisé.") from exc
        if result.returncode:
            raise AudioValidationError("Une partie de l’audio est illisible. Réenregistrez-la avant de réessayer.")

    with TemporaryDirectory(prefix="ruinion-audio-merge-") as temporary:
        workdir = Path(temporary)
        combined = workdir / "combined.pcm"
        pcm_part = workdir / "part.pcm"
        total_bytes = 0
        with combined.open("wb") as output:
            for path, content_type in parts:
                remaining_seconds = MAX_AUDIO_SECONDS - total_bytes / PCM_BYTES_PER_SECOND
                convert([
                    "-protocol_whitelist", "file,pipe", "-f", audio_input_format(content_type),
                    "-i", str(path), "-map", "0:a:0", "-vn",
                    "-t", str(max(0, remaining_seconds) + 1),
                    "-ac", "1", "-ar", "16000", "-f", "s16le", str(pcm_part),
                ])
                size = pcm_part.stat().st_size
                if not size:
                    raise AudioValidationError("Une partie de l’audio est vide.")
                total_bytes += size
                if total_bytes > MAX_AUDIO_SECONDS * PCM_BYTES_PER_SECOND:
                    raise AudioValidationError("La durée totale de l’enregistrement dépasse 4 heures.")
                with pcm_part.open("rb") as source:
                    shutil.copyfileobj(source, output)

        final = workdir / "recording.mp3"
        convert([
            "-protocol_whitelist", "file,pipe", "-f", "s16le", "-ar", "16000", "-ac", "1",
            "-i", str(combined), "-c:a", "libmp3lame", "-b:a", "64k", str(final),
        ])
        return final.read_bytes()
