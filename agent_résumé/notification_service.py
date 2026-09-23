from datetime import datetime, timedelta

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from models import (
    Organization,
    OrganizationInvitation,
    OrganizationMember,
    OrganizationNotification,
)


EXPIRING_SOON = timedelta(days=2)


def _notification_text(kind: str, invitation: OrganizationInvitation) -> tuple[str, str]:
    if kind == "invitation_expiring":
        return (
            "Invitation bientôt expirée",
            f"L'invitation envoyée à {invitation.email} expire bientôt.",
        )
    if kind == "invitation_expired":
        return (
            "Invitation expirée",
            f"L'invitation envoyée à {invitation.email} a expiré.",
        )
    return (
        "Invitation acceptée",
        f"{invitation.email} a rejoint votre organisation.",
    )


def _add_once(
    db: Session,
    *,
    organization_id: int,
    user_id: int,
    invitation: OrganizationInvitation,
    kind: str,
    created_at: datetime,
) -> bool:
    exists = (
        db.query(OrganizationNotification.id)
        .filter(
            OrganizationNotification.user_id == user_id,
            OrganizationNotification.kind == kind,
            OrganizationNotification.invitation_id == invitation.id,
        )
        .first()
    )
    if exists is not None:
        return False

    title, message = _notification_text(kind, invitation)
    db.add(
        OrganizationNotification(
            organization_id=organization_id,
            user_id=user_id,
            invitation_id=invitation.id,
            kind=kind,
            title=title,
            message=message,
            created_at=created_at,
        )
    )
    return True


def schedule_invitation_notifications(
    db: Session,
    organization: Organization,
    invitation: OrganizationInvitation,
) -> int:
    if not organization.invitation_notifications_enabled:
        return 0

    recipients = (
        db.query(OrganizationMember.user_id)
        .filter(
            OrganizationMember.organization_id == organization.id,
            OrganizationMember.status == "active",
            OrganizationMember.role.in_(("owner", "admin")),
        )
        .all()
    )
    created = 0
    now = datetime.utcnow()
    for (user_id,) in recipients:
        for kind in ("invitation_expiring", "invitation_expired"):
            created += int(
                _add_once(
                    db,
                    organization_id=organization.id,
                    user_id=user_id,
                    invitation=invitation,
                    kind=kind,
                    created_at=now,
                )
            )
    return created


def sync_invitation_notifications_for_user(
    db: Session,
    organization: Organization,
    user_id: int,
) -> int:
    if not organization.invitation_notifications_enabled:
        return 0

    invitations = (
        db.query(OrganizationInvitation)
        .filter(
            OrganizationInvitation.organization_id == organization.id,
            OrganizationInvitation.status == "pending",
        )
        .all()
    )
    created = 0
    now = datetime.utcnow()
    for invitation in invitations:
        for kind in ("invitation_expiring", "invitation_expired"):
            created += int(
                _add_once(
                    db,
                    organization_id=organization.id,
                    user_id=user_id,
                    invitation=invitation,
                    kind=kind,
                    created_at=now,
                )
            )
    return created


def notify_invitation_accepted(
    db: Session,
    organization: Organization,
    invitation: OrganizationInvitation,
    *,
    exclude_user_id: int,
) -> int:
    deadline_notifications = db.query(OrganizationNotification).filter(
        OrganizationNotification.organization_id == organization.id,
        OrganizationNotification.invitation_id == invitation.id,
        OrganizationNotification.kind.in_(
            ("invitation_expiring", "invitation_expired")
        ),
        OrganizationNotification.read_at.is_(None),
    )
    deadline_notifications.update(
        {OrganizationNotification.read_at: datetime.utcnow()},
        synchronize_session=False,
    )

    if not organization.invitation_notifications_enabled:
        return 0

    recipients = (
        db.query(OrganizationMember.user_id)
        .filter(
            OrganizationMember.organization_id == organization.id,
            OrganizationMember.status == "active",
            OrganizationMember.role.in_(("owner", "admin")),
            OrganizationMember.user_id != exclude_user_id,
        )
        .all()
    )
    created = 0
    now = datetime.utcnow()
    for (user_id,) in recipients:
        created += int(
            _add_once(
                db,
                organization_id=organization.id,
                user_id=user_id,
                invitation=invitation,
                kind="invitation_accepted",
                created_at=now,
            )
        )
    return created


def mark_invitation_notifications_read(
    db: Session,
    organization_id: int,
    invitation_id: int,
) -> None:
    db.query(OrganizationNotification).filter(
        OrganizationNotification.organization_id == organization_id,
        OrganizationNotification.invitation_id == invitation_id,
        OrganizationNotification.read_at.is_(None),
    ).update(
        {OrganizationNotification.read_at: datetime.utcnow()},
        synchronize_session=False,
    )


def visible_notifications_query(
    db: Session,
    *,
    organization_id: int,
    user_id: int,
):
    now = datetime.utcnow()
    soon = now + EXPIRING_SOON
    return (
        db.query(OrganizationNotification)
        .outerjoin(
            OrganizationInvitation,
            OrganizationInvitation.id == OrganizationNotification.invitation_id,
        )
        .filter(
            OrganizationNotification.organization_id == organization_id,
            OrganizationNotification.user_id == user_id,
            or_(
                OrganizationNotification.kind == "invitation_accepted",
                and_(
                    OrganizationNotification.kind == "invitation_expiring",
                    OrganizationInvitation.status == "pending",
                    OrganizationInvitation.expires_at > now,
                    OrganizationInvitation.expires_at <= soon,
                ),
                and_(
                    OrganizationNotification.kind == "invitation_expired",
                    OrganizationInvitation.status == "pending",
                    OrganizationInvitation.expires_at <= now,
                ),
            ),
        )
    )
