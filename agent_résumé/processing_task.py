"""Isolated stage runner. Only fixed application code executes here.

The parent kills it on timeout. No database writes happen in this process:
the owner checks its lease before saving the returned JSON data.
"""
import json
from pathlib import Path
import math
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

LONG_AUDIO_SECONDS = 15 * 60
TRANSCRIPTION_CHUNK_SECONDS = 10 * 60


def _split_audio(path, duration, directory):
    executable = shutil.which("ffmpeg")
    if not executable:
        raise ValueError("FFmpeg est requis pour découper les enregistrements longs.")
    chunks = []
    for index, offset in enumerate(range(0, math.ceil(duration), TRANSCRIPTION_CHUNK_SECONDS)):
        chunk_duration = min(TRANSCRIPTION_CHUNK_SECONDS, duration - offset)
        target = Path(directory) / f"chunk-{index:03d}.mp3"
        result = subprocess.run([
            executable, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", str(offset), "-i", str(path), "-t", str(chunk_duration),
            "-map", "0:a:0", "-vn", "-c:a", "libmp3lame", "-b:a", "64k", str(target),
        ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=90, check=False)
        if result.returncode or not target.is_file() or not target.stat().st_size:
            raise ValueError("Le découpage de l’enregistrement long a échoué.")
        chunks.append((target, float(offset), float(chunk_duration)))
    return chunks


def _transcribe_recording(path, duration):
    from transcription_service import transcribe_audio_with_segments

    if not duration or duration <= LONG_AUDIO_SECONDS:
        return transcribe_audio_with_segments(
            path.read_bytes(), path.name, "audio/mpeg", expected_duration=duration,
        )
    all_segments = []
    with TemporaryDirectory(prefix="ruinion-transcription-") as directory:
        for chunk, offset, chunk_duration in _split_audio(path, duration, directory):
            result = transcribe_audio_with_segments(
                chunk.read_bytes(), chunk.name, "audio/mpeg",
                expected_duration=chunk_duration, timestamp_offset=offset,
            )
            all_segments.extend(result["transcription_segments"])
    return {"transcription": " ".join(item["text"] for item in all_segments).strip(),
            "transcription_segments": all_segments}


def execute(payload):
    stage = payload["stage"]
    if stage == "preparing":
        from audio_processing import merge_audio_segments
        from meeting_storage import resolve_audio

        parts = [(resolve_audio(part["path"]), part["content_type"]) for part in payload["audio_manifest"]]
        output = parts[0][0].parent / "recording.mp3"
        content = merge_audio_segments(parts)
        temporary = output.with_suffix(".tmp")
        temporary.write_bytes(content)
        temporary.replace(output)
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(output)],
            capture_output=True, check=True, timeout=10,
        )
        duration = float(json.loads(probe.stdout)["format"]["duration"])
        return {"audio_path": str(output), "audio_duration": duration}
    if stage == "transcribing":
        from meeting_storage import resolve_audio

        path = resolve_audio(payload["audio_path"])
        return _transcribe_recording(path, payload.get("audio_duration"))
    if stage == "writing":
        from meeting_content import generate_content
        return generate_content(payload["context"], payload["model"])
    if stage == "building":
        from tools import BuildWord, get_reports_dir

        context = payload["context"]
        filename = f'meeting-{payload["meeting_id"]}-{payload["token"]}'
        expected = get_reports_dir().resolve() / f"{filename}.docx"
        BuildWord().forward(
            title=context["title"], filename=filename, template="meeting_report",
            organization=context["organization"], participants=context["participants"], date=context["date"],
            body=f'RESUME_COURT:\n{payload["summary_short"]}\n\nCOMPTE_RENDU_DETAILLE:\n{payload["summary_long"]}',
        )
        if not expected.is_file() or not expected.stat().st_size:
            raise ValueError("Le document Word n’a pas pu être créé. Les résumés sont conservés.")
        return {"report_path": str(expected)}
    raise ValueError("Étape inconnue.")


def safe_error(error, stage):
    # Never expose provider response bodies, credentials or prompts.
    name = type(error).__name__.lower()
    status = getattr(error, "status_code", None)
    if "validation" in name or "json" in name:
        return "Le modèle a retourné un contenu incomplet ou un format invalide."
    if status == 429 or "ratelimit" in name:
        return "Le fournisseur IA limite les requêtes (429). Réessayez plus tard."
    if status in (401, 403) or "authentication" in name:
        return "Le fournisseur IA refuse l’accès. Vérifiez la clé et les droits du modèle."
    if status == 400:
        return "Le fournisseur IA refuse ce format ou cette taille de requête."
    if "timeout" in name:
        return "Le fournisseur IA n’a pas répondu dans le délai autorisé."
    if "connect" in name:
        return "Connexion au fournisseur IA impossible. Vérifiez la connexion du serveur."
    if isinstance(error, ValueError) and (str(error).startswith("Configuration manquante :") or stage in ("preparing", "building")):
        return str(error)[:300]
    return {"preparing": "L’audio est illisible ou son assemblage a échoué.",
            "transcribing": "La transcription a échoué ou est vide. Vérifiez l’enregistrement puis réessayez.",
            "writing": "La rédaction a échoué ou le modèle a renvoyé une réponse incomplète.",
            "building": "La création du Word a échoué. Les résumés sont conservés."}[stage]


if __name__ == "__main__":
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    try:
        result = {"result": execute(payload)}
    except Exception as error:
        result = {"error": safe_error(error, payload["stage"])}
    Path(sys.argv[2]).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
