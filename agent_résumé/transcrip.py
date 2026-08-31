import os

from mistralai.client import Mistral

DEFAULT_AUDIO_MODEL = "voxtral-mini-latest"

def transcribe_audio(audio_bytes: bytes, file_name: str, content_type: str, language="fr") -> str:
    api_key = os.getenv("MISTRAL_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY est manquant dans le fichier .env")
    
    
    if not audio_bytes:
        raise ValueError("La note vocale est vide.")
    
    file_name = file_name or "note_vocale.wav"
    content_type = content_type or "audio/wav"
    
    client = Mistral(api_key=api_key)
    response = client.audio.transcriptions.complete(
        model=os.getenv("MISTRAL_AUDIO_MODEL", DEFAULT_AUDIO_MODEL),
        file={
            "content": audio_bytes,
            "file_name": file_name,
            "content_type": content_type,
        },
        language=language,
    )
    
    text = getattr(response, "text", "").strip()
    if not text:
        raise RuntimeError("La transcription a échoué")
        
    return text