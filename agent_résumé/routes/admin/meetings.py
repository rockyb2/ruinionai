import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import delete, func, or_
from sqlalchemy.orm import Session, joinedload

from auth.dependencies import require_platform_admin
from database import get_db
from meeting_processing import ACTIVE
from meeting_storage import audio_directory
from models import Meeting, Organization, User
from routes.admin.common import commit, get_record, page
from routes.admin.schemas import MeetingCreate, MeetingUpdate
from routes.meetings import enqueue_summary
from tools import get_reports_dir

router = APIRouter(prefix="/meetings")
logger = logging.getLogger(__name__)
PRIVATE_CONTENT_MESSAGE = (
                    "Le contenu privé des réunions n’est pas accessible "
                    "à l’administration de la plateforme."
                )


def meeting_data(meeting: Meeting, detail: bool = False) -> dict:
    """
    Retourne uniquement les métadonnées nécessaires à l'administration.

    Cette fonction ne doit jamais renvoyer :
    - la transcription ;
    - les segments de transcription ;
    - les résumés ;
    - les participants ;
    - les chemins des fichiers ;
    - le contenu audio ou le document Word.
    """
    creator = meeting.created_by

    data = {
        "id": meeting.id,
        "title": meeting.title,
        "organization_id": meeting.organization_id,
        "organization_name": meeting.organization.name,
        "created_by_user_id": meeting.created_by_user_id,
        "created_by_name": (
            " ".join(
                filter(
                    None,
                    [creator.first_name, creator.last_name],
                )
            )
            if creator
            else "Compte supprimé"
        ),
        "date": meeting.date,
        "created_at": meeting.created_at,
        "updated_at": meeting.updated_at,
        "audio_duration": meeting.audio_duration,
        "audio_available": meeting.audio_available,
        "has_source_audio": meeting.has_source_audio,
        "has_transcription": bool(meeting.transcription),
        "has_summary": bool(meeting.summary_short and meeting.summary_long),
        "has_report": bool(meeting.report_path),
        "processing_status": meeting.processing_status,
    }

    if detail:
        data["processing_error"] = meeting.processing_error

    return data


@router.get("")
def list_meetings(
    q: str = Query("", max_length=150),
    organization_id: int | None = Query(None, gt=0),
    user_id: int | None = Query(None, gt=0),
    status: str = Query("", max_length=24),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Meeting)
        .join(Organization)
        .options(joinedload(Meeting.organization), joinedload(Meeting.created_by))
    )
    if q.strip():
        query = query.filter(
            or_(
                Meeting.title.icontains(q.strip(), autoescape=True),
                Organization.name.icontains(q.strip(), autoescape=True),
            )
        )
    if organization_id:
        query = query.filter(Meeting.organization_id == organization_id)
    if user_id:
        query = query.filter(Meeting.created_by_user_id == user_id)
    if status:
        query = query.filter(Meeting.processing_status == status)
    result = page(
        query.order_by(Meeting.created_at.desc(), Meeting.id.desc()),
        offset,
        limit,
        meeting_data,
    )
    result["stats"] = {
        "total": db.query(Meeting).count(),
        "completed": db.query(Meeting).filter_by(processing_status="completed").count(),
        "failed": db.query(Meeting).filter_by(processing_status="failed").count(),
        "active": db.query(Meeting)
        .filter(Meeting.processing_status.in_(ACTIVE))
        .count(),
        "audio_seconds": db.query(
            func.coalesce(func.sum(Meeting.audio_duration), 0)
        ).scalar(),
    }
    return result


@router.post("", status_code=201)
def create_meeting(
    payload: MeetingCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_platform_admin),
):
    get_record(db, Organization, payload.organization_id, lock=True)
    meeting = Meeting(
        organization_id=payload.organization_id,
        title=payload.title,
        created_by_user_id=actor.id,
    )
    db.add(meeting)
    commit(db)
    return meeting_data(meeting, True)


@router.get("/{meeting_id}")
def read_meeting(meeting_id: int, db: Session = Depends(get_db)):
    return meeting_data(get_record(db, Meeting, meeting_id), True)


@router.patch("/{meeting_id}")
def update_meeting(
    meeting_id: int, payload: MeetingUpdate, db: Session = Depends(get_db)
):
    meeting = get_record(db, Meeting, meeting_id, lock=True)
    if meeting.processing_status in ACTIVE:
        raise HTTPException(
            409, "Attendez la fin du traitement avant de modifier cette réunion."
        )
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(meeting, key, value)
    commit(db)
    return meeting_data(meeting, True)


@router.post("/{meeting_id}/summary", status_code=202)
def retry_meeting(meeting_id: int, response: Response, db: Session = Depends(get_db)):
    meeting = get_record(db, Meeting, meeting_id, lock=True)
    return meeting_data(enqueue_summary(meeting, response, db), True)


@router.get("/{meeting_id}/audio")
def audio(
    meeting_id: int,
    db: Session = Depends(get_db),
):
    get_record(db, Meeting, meeting_id)

    raise HTTPException(
        status_code=403,
        detail=PRIVATE_CONTENT_MESSAGE,
    )

@router.get("/{meeting_id}/report")
def report(
    meeting_id: int,
    db: Session = Depends(get_db),
):
    get_record(db, Meeting, meeting_id)

    raise HTTPException(
        status_code=403,
        detail=PRIVATE_CONTENT_MESSAGE,
    )


@router.delete("/{meeting_id}", status_code=204)
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = get_record(db, Meeting, meeting_id, lock=True)
    if meeting.processing_status in ACTIVE:
        raise HTTPException(
            409, "Attendez la fin du traitement avant de supprimer cette réunion."
        )
    files = [
        (meeting.audio_path, audio_directory()),
        (meeting.report_path, get_reports_dir().resolve()),
    ]
    files += [
        (part.get("path"), audio_directory())
        for part in (meeting.audio_manifest or [])
        if isinstance(part, dict)
    ]
    db.execute(delete(Meeting).where(Meeting.id == meeting.id))
    commit(db)
    # Ne supprimer que des fichiers explicitement rattachés à la réunion,
    # contenus dans les répertoires de stockage, jamais un dossier récursif.
    for value, root in files:
        if not value:
            continue
        path = Path(value).resolve()
        if path.is_relative_to(root) and path.is_file():
            try:
                path.unlink(missing_ok=True)
            except OSError:
                logger.exception(
                    "Nettoyage du fichier de la réunion %s impossible", meeting_id
                )
                
    return Response(status_code=204)
