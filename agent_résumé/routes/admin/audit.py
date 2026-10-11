from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models import AuditLog, User


router = APIRouter(prefix="/audit")


def audit_data(entry: AuditLog, actors: dict[int, User] | None = None) -> dict:
    actor = (actors or {}).get(entry.actor_id)
    return {
        "id": entry.id,
        "actor_id": entry.actor_id,
        "actor_name": (
            " ".join(filter(None, [actor.first_name, actor.last_name]))
            if actor
            else None
        ),
        "actor_email": actor.email if actor else None,
        "action": entry.action,
        "target_type": entry.target_type,
        "target_id": entry.target_id,
        "method": entry.method,
        "path": entry.path,
        "status_code": entry.status_code,
        "ip_hash": entry.ip_hash,
        "details": entry.details or {},
        "created_at": entry.created_at,
    }


@router.get("")
def list_audit_logs(
    action: str = Query("", max_length=80),
    actor_id: int | None = Query(None, gt=0),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    base_query = db.query(AuditLog)
    query = base_query
    if action.strip():
        query = query.filter(AuditLog.action == action.strip())
    if actor_id:
        query = query.filter(AuditLog.actor_id == actor_id)
    total = query.count()
    entries = (
        query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    actor_ids = {entry.actor_id for entry in entries if entry.actor_id is not None}
    actors = (
        {
            actor.id: actor
            for actor in db.query(User).filter(User.id.in_(actor_ids)).all()
        }
        if actor_ids
        else {}
    )

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": [audit_data(entry, actors) for entry in entries],
        "stats": {
            "total": base_query.count(),
            "successful": base_query.filter(
                AuditLog.status_code >= 200,
                AuditLog.status_code < 400,
            ).count(),
            "failed": base_query.filter(AuditLog.status_code >= 400).count(),
            "authentication": base_query.filter(
                AuditLog.action.like("AUTH_%")
            ).count(),
        },
    }
