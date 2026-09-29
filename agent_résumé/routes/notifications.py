from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from sqlalchemy.orm import Session

from auth.dependencies import AuthContext, get_auth_context, require_organization_admin
from database import get_db
from models import OrganizationNotification
from notification_service import (
    sync_invitation_notifications_for_user,
    visible_notifications_query,
)
from schema import (
    NotificationSyncRead,
    OrganizationNotificationRead,
    OrganizationNotificationsPage,
)


router = APIRouter(
    prefix="/organization/notifications",
    tags=["organization"],
)


def notifications_for_user(db: Session, auth: AuthContext):
    return visible_notifications_query(
        db,
        organization_id=auth.membership.organization_id,
        user_id=auth.user.id,
        include_organization_invitations=(
            auth.membership.role in ("owner", "admin")
            and auth.membership.organization.invitation_notifications_enabled
        ),
    )


@router.post("/sync", response_model=NotificationSyncRead)
def sync_notifications(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_organization_admin),
):
    try:
        created = sync_invitation_notifications_for_user(
            db,
            auth.membership.organization,
            auth.user.id,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"created": created}


@router.get("", response_model=OrganizationNotificationsPage)
def list_notifications(
    response: Response,
    unread_only: bool = Query(default=False),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    query = notifications_for_user(db, auth)
    unread_count = query.filter(
        OrganizationNotification.read_at.is_(None)
    ).count()
    if unread_only:
        query = query.filter(OrganizationNotification.read_at.is_(None))

    total = query.count()
    items = (
        query.order_by(OrganizationNotification.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    response.headers["Cache-Control"] = "no-store"
    return {
        "items": items,
        "total": total,
        "unread_count": unread_count,
        "offset": offset,
        "limit": limit,
    }


@router.patch(
    "/{notification_id}/read",
    response_model=OrganizationNotificationRead,
)
def mark_notification_read(
    response: Response,
    notification_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    notification = (
        notifications_for_user(db, auth)
        .filter(
            OrganizationNotification.id == notification_id,
        )
        .first()
    )
    if notification is None:
        raise HTTPException(404, "Notification introuvable.")

    if notification.read_at is None:
        notification.read_at = datetime.utcnow()
        db.commit()
        db.refresh(notification)

    response.headers["Cache-Control"] = "no-store"
    return notification


@router.post("/read-all", status_code=204)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    query = notifications_for_user(db, auth).filter(OrganizationNotification.read_at.is_(None))
    notification_ids = [item.id for item in query.all()]
    if notification_ids:
        db.query(OrganizationNotification).filter(
            OrganizationNotification.id.in_(notification_ids)
        ).update(
            {OrganizationNotification.read_at: datetime.utcnow()},
            synchronize_session=False,
        )
        db.commit()
    return Response(status_code=204)
