from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool
from sqlalchemy import func, or_, update
from sqlalchemy.orm import Session, joinedload

from auth.dependencies import AuthContext, get_auth_context
from audio_processing import AudioValidationError, MAX_AUDIO_BYTES, MAX_AUDIO_SEGMENTS, audio_input_format
from database import get_db
from meeting_processing import ACTIVE
from meeting_storage import audio_directory, resolve_audio
from models import Meeting, MeetingParticipant, OrganizationMember, OrganizationNotification, User
from schema import MeetingCreate, MeetingInviteesPage, MeetingRead
from tools import get_reports_dir

router = APIRouter()


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
        raise HTTPException(status_code=404, detail="Réunion introuvable.")

    return db_meeting


def resolve_report_path(report_path: str | None) -> Path:
    if not report_path:
        raise HTTPException(status_code=404, detail="Le compte rendu n’a pas encore été généré.")

    reports_dir = get_reports_dir().resolve()
    file_path = Path(report_path).resolve()

    if not file_path.is_relative_to(reports_dir) or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Compte rendu introuvable.")

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
    organization_id = auth_context.membership.organization_id
    try:
        members = (
            db.query(OrganizationMember)
            .join(OrganizationMember.user)
            .options(joinedload(OrganizationMember.user))
            .filter(
                OrganizationMember.id.in_(meeting.participant_member_ids),
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.status == "active",
                User.is_active.is_(True),
            )
            .all()
        ) if meeting.participant_member_ids else []
        by_id = {member.id: member for member in members}
        if len(by_id) != len(meeting.participant_member_ids):
            raise HTTPException(422, "Sélectionnez uniquement des membres actifs de votre équipe.")

        invitees = [by_id[member_id] for member_id in meeting.participant_member_ids
                    if member_id != auth_context.membership.id]
        organizer_name = member_name(auth_context.user)
        db_meeting = Meeting(
            title=meeting.title,
            organization_id=organization_id,
            created_by_user_id=auth_context.user.id,
            participants=", ".join([organizer_name, *[member_name(member.user) for member in invitees]]),
            invited_members=[MeetingParticipant(member_id=member.id) for member in invitees],
        )
        db.add(db_meeting)
        db.flush()
        for member in invitees:
            db.add(OrganizationNotification(
                organization_id=organization_id,
                user_id=member.user_id,
                meeting_id=db_meeting.id,
                kind="meeting_invitation",
                title="Invitation à une réunion",
                message=f'{organizer_name[:150]} vous invite à la réunion « {meeting.title} ».',
            ))
        db.commit()
        db.refresh(db_meeting)
    except Exception:
        db.rollback()
        raise
    return db_meeting


def member_name(user: User) -> str:
    return " ".join(part for part in (user.first_name, user.last_name) if part).strip() or user.email


@router.get("/meetings/invitees", response_model=MeetingInviteesPage)
def list_meeting_invitees(
    response: Response,
    q: str = Query(default="", max_length=100),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    query = db.query(OrganizationMember).join(OrganizationMember.user).filter(
        OrganizationMember.organization_id == auth_context.membership.organization_id,
        OrganizationMember.status == "active",
        OrganizationMember.user_id != auth_context.user.id,
        User.is_active.is_(True),
    )
    if q.strip():
        query = query.filter(or_(
            (func.coalesce(User.first_name, "") + " " + func.coalesce(User.last_name, "")).icontains(q.strip(), autoescape=True),
            User.email.icontains(q.strip(), autoescape=True),
        ))
    total = query.count()
    members = query.options(joinedload(OrganizationMember.user)).order_by(OrganizationMember.id).offset(offset).limit(limit).all()
    response.headers["Cache-Control"] = "no-store"
    return {
        "items": [{"member_id": member.id, "name": member_name(member.user), "email": member.user.email} for member in members],
        "total": total, "offset": offset, "limit": limit,
    }


@router.get("/meetings/{meeting_id}", response_model=MeetingRead)
def read_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    return get_meeting_for_current_org(meeting_id, db, auth_context)


@router.post("/meetings/{meeting_id}/audio", response_model=MeetingRead, status_code=202)
async def upload_audio(
    meeting_id: int,
    file: UploadFile | None = File(None),
    files: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    meeting = get_meeting_for_current_org(meeting_id, db, auth_context)
    if (file is None) == (not files):
        raise HTTPException(400, "Envoyez un fichier audio ou les parties d’un enregistrement.")
    uploads = files if files else [file]
    directory = None
    saved = False
    try:
        if len(uploads) > MAX_AUDIO_SEGMENTS:
            raise HTTPException(400, "Un enregistrement ne peut pas dépasser 100 parties.")
        # An HTTP retry reuses the persisted source and its existing task.
        if meeting.has_source_audio:
            return meeting
        if meeting.transcription or meeting.processing_status in ACTIVE:
            raise HTTPException(409, "Cette réunion possède déjà une transcription. Créez une nouvelle réunion pour un autre audio.")
        directory = audio_directory() / f"org-{meeting.organization_id}" / f"meeting-{meeting.id}" / uuid4().hex
        directory.mkdir(parents=True)
        manifest, total_bytes = [], 0
        for index, upload in enumerate(uploads):
            content_type = (upload.content_type or "").split(";")[0].lower()
            audio_input_format(content_type)
            path = directory / f"part-{index}"
            size = 0
            with path.open("wb") as target:
                while chunk := await upload.read(1024 * 1024):
                    total_bytes += len(chunk)
                    size += len(chunk)
                    if total_bytes > MAX_AUDIO_BYTES:
                        raise HTTPException(413, "La taille totale de l’audio dépasse 500 Mo.")
                    await run_in_threadpool(target.write, chunk)
            if not size:
                raise AudioValidationError("Une partie de l’audio est vide.")
            manifest.append({"path": str(path), "content_type": content_type})
        # Atomic compare-and-set: concurrent uploads cannot replace an accepted source.
        count = db.execute(update(Meeting).where(
            Meeting.id == meeting.id, Meeting.audio_manifest.is_(None),
            Meeting.transcription.is_(None), Meeting.processing_status.not_in(ACTIVE),
        ).values(audio_manifest=manifest, processing_status="queued", processing_error=None)).rowcount
        db.commit()
        saved = count == 1
        db.refresh(meeting)
        return meeting
    except AudioValidationError as error:
        raise HTTPException(422, str(error)) from error
    finally:
        for upload in uploads:
            await upload.close()
        if directory and not saved:
            # Only this request's newly created, known directory is removed.
            for part in directory.iterdir():
                part.unlink()
            directory.rmdir()


@router.post("/meetings/{meeting_id}/summary", response_model=MeetingRead, status_code=202)
def summarize_meeting(
    meeting_id: int,
    response: Response,
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    meeting = get_meeting_for_current_org(meeting_id, db, auth_context)
    return enqueue_summary(meeting, response, db)


def enqueue_summary(meeting: Meeting, response: Response, db: Session):
    """File de traitement commune à l'espace équipe et à l'administration."""
    if meeting.processing_status in ACTIVE:
        return meeting
    if not meeting.transcription and not meeting.has_source_audio:
        raise HTTPException(400, "Ajoutez un enregistrement avant de lancer la génération.")
    if meeting.summary_short and meeting.summary_long and meeting.report_path:
        try:
            resolve_report_path(meeting.report_path)
            response.status_code = 200
            return meeting
        except HTTPException:
            pass  # The text is retained; recreate only the missing Word.
    db.execute(update(Meeting).where(
        Meeting.id == meeting.id, Meeting.processing_status == meeting.processing_status,
        Meeting.updated_at == meeting.updated_at,
    ).values(processing_status="queued", processing_error=None,
             processing_token=None, processing_expires_at=None))
    db.commit()
    db.refresh(meeting)
    return meeting


@router.get("/meetings/{meeting_id}/audio")
def read_meeting_audio(
    meeting_id: int,
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    meeting = get_meeting_for_current_org(meeting_id, db, auth_context)
    if not meeting.audio_path:
        raise HTTPException(404, "Aucun audio conservé pour cette réunion.")
    try:
        path = resolve_audio(meeting.audio_path)
    except ValueError as error:
        raise HTTPException(404, str(error)) from error
    return FileResponse(path, media_type="audio/mpeg", filename=f"reunion-{meeting.id}.mp3",
                        content_disposition_type="inline", headers={"Cache-Control": "private, no-store"})


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
