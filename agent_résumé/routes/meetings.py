from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Meeting, User
from transcrip import transcribe_audio
from agent import create_agent
from fastapi import UploadFile, File
from schema import MeetingCreate, MeetingRead
import os
from time import sleep
router = APIRouter()

MODELS = [
    os.getenv("MISTRAL_MODEL_ID"),
    os.getenv("MISTRAL_MODEL_ID2"),
    os.getenv("ZAI_MODEL"),
]

MODELS = [model for model in MODELS if model]

def run_with_model_fallback(prompt):
    last_error = None
    for model_id in MODELS:
        try:
            agent = create_agent(model_id)
            return agent.run(prompt)
        except Exception as error:
            last_error = error
            print(f"Modèle échoué : {model_id} -> {error}")

    raise RuntimeError(f"Aucun modèle disponible : {last_error}")




def run_with_retries(action, operation_name: str, attempts: int = 3):
    last_error = None

    for attempt in range(1, attempts + 1):
        try:
            return action()
        except Exception as exc:
            last_error = exc
            if attempt < attempts:
                sleep(2 * attempt)

    raise HTTPException(
        status_code=502,
        detail=f"{operation_name} a echoue apres {attempts} essais : {last_error}",
    )


# api endpoints for meetings
@router.post("/meetings/", response_model=MeetingRead)
def create_meeting(meeting: MeetingCreate, db: Session = Depends(get_db)):
    db_meeting = Meeting(
        title=meeting.title,
        participants=",".join(meeting.participants) if meeting.participants else None
    )
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting

@router.get("/meetings/{meeting_id}", response_model=MeetingRead)
def read_meeting(meeting_id: int, db: Session = Depends(get_db)):
    db_meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if db_meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return db_meeting

@router.post("/meetings/{meeting_id}/audio", response_model=MeetingRead)
async def upload_audio(meeting_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    db_meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if db_meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    audio_bytes = await file.read()
        
    transcription = run_with_retries(
        lambda: transcribe_audio(
            audio_bytes=audio_bytes,
            file_name=file.filename,
            content_type=file.content_type,
            language="fr",
        ),
        "La transcription Mistral",
    )
    
    db_meeting.transcription = transcription
    db.commit()
    db.refresh(db_meeting)
    return db_meeting

@router.post("/meetings/{meeting_id}/summary", response_model=MeetingRead)
def  summarize_meeting(meeting_id: int, db: Session = Depends(get_db)):
    db_meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if db_meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if not db_meeting.transcription:
        raise HTTPException(status_code=400, detail="Transcription not available for this meeting")
    # Generate a summary from the transcription
    transcription= db_meeting.transcription
    
    prompt_resume = f"""
    Tu dois faire un résumé professionnel de cette réunion.
    
    À partir de la transcription ci-dessous, produis :
    
        1. Résumé court
        2. Points importants
        3. Décisions prises
        4. Actions à faire
        5. Questions ouvertes
    
        N'invente rien. Si une information n'est pas présente, écris "Non précisé".
    
        Transcription :
        {transcription}
        """
        
    summary = run_with_retries(
    lambda: run_with_model_fallback(prompt_resume),
    "La génération du résumé"
)
    db_meeting.summary = summary
    db.commit()
    db.refresh(db_meeting)
    return db_meeting


