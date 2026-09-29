"""Private files; paths never come from a model or a client filename."""
import os
from pathlib import Path


def audio_directory():
    path = Path(os.getenv("AUDIO_DIR", str(Path(__file__).parent / "storage" / "audio"))).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_audio(path):
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(audio_directory()) or not resolved.is_file():
        raise ValueError("L’enregistrement est introuvable sur le serveur.")
    return resolved
