"""Durable queue on the meeting row, with atomic claims and fenced writes."""
import asyncio
from datetime import datetime, timedelta
import json
import logging
import math
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4

from sqlalchemy import update
from database import SessionLocal
from meeting_content import configured_models
from models import Meeting

from meeting_crypto import (
    decrypt_meeting_value,
    encrypt_meeting_values,
)

logger = logging.getLogger(__name__)
RUNNING = ("preparing", "transcribing", "writing", "building")
ACTIVE = ("queued", *RUNNING)
TIMEOUTS = {"preparing": 330, "transcribing": 90, "writing": 30, "building": 60}
TRANSCRIPTION_CHUNK_SECONDS = 10 * 60
USER_STAGE_ERRORS = {
    "preparing": "Nous n’avons pas pu préparer l’enregistrement. Réessayez.",
    "transcribing": "La transcription n’a pas pu être terminée. Réessayez dans quelques instants.",
    "writing": "Le résumé et le compte rendu n’ont pas pu être générés. Réessayez dans quelques instants.",
    "building": "Le document Word n’a pas pu être créé. Vos textes sont conservés.",
}


class StageError(RuntimeError):
    pass


async def run_stage(payload, timeout):
    with TemporaryDirectory(prefix="ruinion-stage-") as directory:
        request = Path(directory) / "request.json"
        response = Path(directory) / "response.json"
        request.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        process = await asyncio.create_subprocess_exec(
            sys.executable, str(Path(__file__).with_name("processing_task.py")), str(request), str(response),
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            await asyncio.wait_for(process.wait(), timeout=timeout)
        except (asyncio.TimeoutError, asyncio.CancelledError) as error:
            if process.returncode is None:
                process.kill()
            await process.wait()
            if isinstance(error, asyncio.CancelledError):
                raise
            raise StageError(f"Délai de {timeout} secondes dépassé pour cette étape.") from error
        if process.returncode or not response.is_file():
            raise StageError("Le traitement a été interrompu. Vous pouvez le relancer.")
        data = json.loads(response.read_text(encoding="utf-8"))
        if "error" in data:
            raise StageError(data["error"])
        return data["result"]


def next_stage(meeting):
    if not meeting.transcription:
        return "transcribing" if meeting.audio_path else "preparing"
    if not (meeting.summary_short and meeting.summary_long):
        return "writing"
    return "building"


def stage_timeout(stage, audio_duration=None):
    if stage == "transcribing" and audio_duration:
        chunks = max(1, math.ceil(float(audio_duration) / TRANSCRIPTION_CHUNK_SECONDS))
        return TIMEOUTS[stage] * chunks + 30
    return TIMEOUTS[stage]


def stage_lease(stage, audio_duration=None):
    attempts = max(len(configured_models()), 1) if stage == "writing" else 1
    seconds = stage_timeout(stage, audio_duration) * attempts + 30
    return datetime.utcnow() + timedelta(seconds=seconds)


def recover_expired(session_factory=SessionLocal):
    with session_factory() as db:
        db.execute(update(Meeting).where(
            Meeting.processing_status.in_(RUNNING), Meeting.processing_expires_at < datetime.utcnow(),
        ).values(processing_status="failed", processing_token=None, processing_expires_at=None,
                 processing_error="Le traitement a été interrompu sur le serveur. Relancez-le : les étapes sauvegardées seront conservées."))
        db.commit()


def claim_next(session_factory=SessionLocal):
    with session_factory() as db:
        candidate = db.query(Meeting).filter(Meeting.processing_status == "queued").order_by(Meeting.updated_at, Meeting.id).first()
        if candidate is None:
            return None
        meeting_id, stage, token = candidate.id, next_stage(candidate), uuid4().hex
        claimed = db.execute(update(Meeting).where(Meeting.id == meeting_id, Meeting.processing_status == "queued").values(
            processing_status=stage, processing_token=token,
            processing_expires_at=stage_lease(stage, candidate.audio_duration), processing_error=None,
        )).rowcount
        db.commit()
        return (meeting_id, token) if claimed else None


def save_owned(meeting_id, token, values, session_factory=SessionLocal):
    with session_factory() as db:
        organization_id = (
            db.query(Meeting.organization_id)
            .filter(
                Meeting.id == meeting_id,
                Meeting.processing_token == token,
                Meeting.processing_status.in_(RUNNING),
            )
            .scalar()
        )
        
        if organization_id is None:
            raise StageError("Ce traitement n'est plus actif.")
        
        protected_values = encrypt_meeting_values(
            organization_id=organization_id,
            meeting_id=meeting_id,
            values=values,
        )
        
        count = db.execute(
            update(Meeting)
            .where(
                Meeting.id == meeting_id,
                Meeting.processing_token == token,
                Meeting.processing_status.in_(RUNNING),
            )
            .values(**protected_values)
        ).rowcount
        
        db.commit()
        
        if count != 1:
            raise StageError("Ce traitement n’est plus actif.")



async def process_claim(meeting_id, token, session_factory=SessionLocal, runner=run_stage):
    try:
        while True:
            with session_factory() as db:
                meeting = db.get(Meeting, meeting_id)
                if not meeting or meeting.processing_token != token or meeting.processing_status not in RUNNING:
                    return
                
                stage = meeting.processing_status

                transcription = decrypt_meeting_value(
                    meeting,
                    "transcription",
                    allow_legacy_plaintext=True,
                )

                summary_short = decrypt_meeting_value(
                    meeting,
                    "summary_short",
                    allow_legacy_plaintext=True,
                )

                summary_long = decrypt_meeting_value(
                    meeting,
                    "summary_long",
                    allow_legacy_plaintext=True,
                )

                context = {
                    "title": meeting.title,
                    "organization": meeting.organization.name,
                    "participants": meeting.participants or "Non précisé",
                    "date": (meeting.date or meeting.created_at).strftime(
                        "%d/%m/%Y %H:%M"
                    ),
                    "transcription": transcription,
                }

                payload = {
                    "stage": stage,
                    "meeting_id": meeting_id,
                    "token": token,
                    "context": context,
                    "audio_manifest": meeting.audio_manifest,
                    "audio_path": meeting.audio_path,
                    "audio_duration": meeting.audio_duration,
                    "summary_short": summary_short,
                    "summary_long": summary_long,
                }


            logger.info("Meeting %s: %s", meeting_id, stage)
            if stage == "writing":
                models = configured_models()
                if not models:
                    raise StageError("Aucun modèle de rédaction n’est configuré sur le serveur.")
                failures = []
                for model in models:
                    try:
                        result = await runner({**payload, "model": model}, TIMEOUTS[stage])
                        break
                    except StageError as error:
                        logger.warning("Meeting %s: model %s failed (%s)", meeting_id, model, str(error))
                        failures.append(f"{model} : {error}")
                else:
                    logger.warning("Meeting %s: all %s writing models failed: %s",
                                   meeting_id, len(models), " / ".join(failures))
                    raise StageError(USER_STAGE_ERRORS["writing"])
            else:
                result = await runner(payload, stage_timeout(stage, payload.get("audio_duration")))
            following = {"preparing": "transcribing", "transcribing": "writing", "writing": "building", "building": "completed"}[stage]
            # This text transaction commits before Word is ever invoked.
            save_owned(meeting_id, token, {
                **result, "processing_status": following, "processing_error": None,
                "processing_expires_at": stage_lease(
                    following, result.get("audio_duration", payload.get("audio_duration"))
                ) if following in RUNNING else None,
                "processing_token": token if following in RUNNING else None,
            }, session_factory)
            if following == "completed":
                return
    except asyncio.CancelledError:
        try:
            save_owned(meeting_id, token, {"processing_status": "failed", "processing_token": None,
                "processing_expires_at": None, "processing_error": "Le serveur a redémarré. Relancez le traitement pour reprendre les étapes restantes."}, session_factory)
        except Exception:
            pass  # Lease recovery handles database unavailability.
        raise
    except Exception as error:
        technical_message = str(error)
        message = (technical_message if isinstance(error, StageError) and technical_message in USER_STAGE_ERRORS.values()
                   else USER_STAGE_ERRORS.get(locals().get("stage"),
                                              "Le traitement n’a pas pu être terminé. Réessayez dans quelques instants."))
        logger.warning("Meeting %s failed during %s (%s): %s",
                       meeting_id, locals().get("stage", "unknown"), type(error).__name__, technical_message)
        try:
            save_owned(meeting_id, token, {"processing_status": "failed", "processing_error": message,
                "processing_token": None, "processing_expires_at": None}, session_factory)
        except Exception:
            logger.warning("Meeting %s: failed to save status; lease recovery pending", meeting_id)


async def worker_loop():
    while True:
        try:
            recover_expired()
            claim = claim_next()
            if claim:
                await process_claim(*claim)
            else:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            logger.warning("Meeting worker unavailable (%s)", type(error).__name__)
            await asyncio.sleep(5)
