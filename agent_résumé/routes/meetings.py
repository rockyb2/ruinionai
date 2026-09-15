import os
import re
import unicodedata
from uuid import uuid4
from pathlib import Path
from time import sleep

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from auth.dependencies import AuthContext, get_auth_context
from database import get_db
from models import Meeting
from schema import MeetingCreate, MeetingRead
from tools import get_reports_dir
from transcrip import transcribe_audio


router = APIRouter()

MODELS = [
    os.getenv("OPENROUTER_MODEL_ID") or os.getenv("OPENROUTER_MODEL"),
    os.getenv("NEX_AGI_MODEL_ID"),
    os.getenv("NEX_AGI_MODEL_ID2"),
    # os.getenv("MISTRAL_MODEL_ID2"),
    # os.getenv("MISTRAL_MODEL_ID3"),
    # os.getenv("ZAI_MODEL"),
]
MODELS = [model for model in MODELS if model]


def build_report_filename_stem(meeting_id: int, title: str) -> str:
    normalized_title = unicodedata.normalize("NFKD", title or "")
    ascii_title = normalized_title.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", ascii_title.strip().lower()).strip("-")
    slug = slug[:60] or "compte-rendu"
    return f"meeting-{meeting_id}-{slug}-{uuid4().hex[:8]}"


def get_meeting_for_current_org(
    meeting_id: int,
    db: Session,
    auth_context: AuthContext,
) -> Meeting:
    db_meeting = (
        db.query(Meeting)
        .filter(
            Meeting.id == meeting_id,
            Meeting.organization_id == auth_context.membership.organization_id,
        )
        .first()
    )
    if db_meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return db_meeting


def run_with_model_fallback(prompt):
    from agent import create_agent

    if not MODELS:
        raise RuntimeError(
            "Aucun modele configure. Verifie OPENROUTER_MODEL_ID, "
            "NEX_AGI_MODEL_ID ou NEX_AGI_MODEL_ID2 dans l'environnement Docker."
        )

    last_error = None

    for model_id in MODELS:
        try:
            agent = create_agent(model_id)
            return agent.run(prompt)
        except Exception as error:
            last_error = error
            print(f"Modele echoue : {model_id} -> {error}")

    raise RuntimeError(f"Aucun modele disponible : {last_error}")


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


def split_summary_output(output: str) -> tuple[str, str]:
    output = str(output or "")

    short_match = re.search(
        r"RESUME_COURT\s*:\s*(.*?)(?:COMPTE_RENDU_DETAILLE\s*:|$)",
        output,
        flags=re.IGNORECASE | re.DOTALL,
    )
    long_match = re.search(
        r"COMPTE_RENDU_DETAILLE\s*:\s*(.*?)(?:WORD_PATH\s*:|$)",
        output,
        flags=re.IGNORECASE | re.DOTALL,
    )

    summary_short = short_match.group(1).strip() if short_match else ""
    summary_long = long_match.group(1).strip() if long_match else ""

    if not summary_short and not summary_long:
        return output.strip(), output.strip()

    return summary_short or "Non precise", summary_long or output.strip()


def resolve_report_path(report_path: str | None) -> Path:
    if not report_path:
        raise HTTPException(status_code=404, detail="Report not generated")

    reports_dir = get_reports_dir().resolve()
    file_path = Path(report_path).resolve()

    if not file_path.is_relative_to(reports_dir) or not file_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    return file_path


@router.get("/meetings/", response_model=list[MeetingRead])
def list_meetings(
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    return (
        db.query(Meeting)
        .filter(Meeting.organization_id == auth_context.membership.organization_id)
        .order_by(Meeting.created_at.desc(), Meeting.id.desc())
        .all()
    )


@router.post("/meetings/", response_model=MeetingRead)
def create_meeting(
    meeting: MeetingCreate,
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    db_meeting = Meeting(
        title=meeting.title,
        organization_id=auth_context.membership.organization_id,
        created_by_user_id=auth_context.user.id,
        participants=",".join(meeting.participants) if meeting.participants else None,
    )
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting


@router.get("/meetings/{meeting_id}", response_model=MeetingRead)
def read_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    return get_meeting_for_current_org(meeting_id, db, auth_context)


@router.post("/meetings/{meeting_id}/audio", response_model=MeetingRead)
async def upload_audio(
    meeting_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    db_meeting = get_meeting_for_current_org(meeting_id, db, auth_context)
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
def summarize_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    db_meeting = get_meeting_for_current_org(meeting_id, db, auth_context)

    if not db_meeting.transcription:
        raise HTTPException(
            status_code=400,
            detail="Transcription not available for this meeting",
        )

    transcription = db_meeting.transcription
    report_filename = build_report_filename_stem(db_meeting.id, db_meeting.title)
    expected_report_path = (get_reports_dir() / f"{report_filename}.docx").resolve()
    organization_name = auth_context.membership.organization.name
    participants = db_meeting.participants or "Non precise"
    meeting_date = (db_meeting.created_at or db_meeting.date).strftime("%d/%m/%Y %H:%M")

    prompt_summary = f"""
    Tu es l'agent IA de Ruinion AI. Tu dois analyser cette reunion, produire les
    resumes, puis utiliser ton outil BuildWord pour generer le document Word final.

    Tu dois imperativement appeler l'outil BuildWord.
    Le fichier Word doit etre cree avec filename="{report_filename}".
    N'ajoute pas l'extension .docx dans filename.

    Parametres du compte rendu :
    - Organisation : {organization_name}
    - Titre de reunion : {db_meeting.title}
    - Date : {meeting_date}
    - Participants : {participants}

    Le document Word doit etre professionnel et contenir :
    1. Titre du document
    2. Informations de reunion
    3. Resume court
    4. Compte rendu detaille
    5. Decisions prises
    6. Actions a faire
    7. Questions ouvertes
    8. Transcription source en annexe

    A partir de la transcription ci-dessous, produis :

    RESUME_COURT:
    - Un resume de 5 a 10 lignes
    - Les decisions importantes si elles existent
    - Les actions urgentes si elles existent

    COMPTE_RENDU_DETAILLE:
    1. Resume long
    2. Points importants
    3. Decisions prises
    4. Actions a faire
    5. Questions ouvertes
    6. Risques ou blocages

    N'invente rien. Si une information n'est pas presente, ecris "Non precise".
    Apres avoir appele BuildWord, ta reponse finale doit respecter exactement ce format :

    RESUME_COURT:
    ...

    COMPTE_RENDU_DETAILLE:
    ...

    WORD_PATH:
    chemin du fichier retourne par BuildWord

    Transcription :
    {transcription}
    """

    summary_output = run_with_retries(
        lambda: run_with_model_fallback(prompt_summary),
        "La generation des resumes",
        attempts=1,
    )
    summary_short, summary_long = split_summary_output(summary_output)

    db_meeting.summary_short = summary_short
    db_meeting.summary_long = summary_long
    if not expected_report_path.exists():
        raise HTTPException(
            status_code=502,
            detail="L'agent a genere le resume mais n'a pas cree le document Word avec BuildWord.",
        )

    db_meeting.report_path = str(expected_report_path)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting


@router.get("/meetings/{meeting_id}/report")
def download_meeting_report(
    meeting_id: int,
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    db_meeting = get_meeting_for_current_org(meeting_id, db, auth_context)
    file_path = resolve_report_path(db_meeting.report_path)

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
