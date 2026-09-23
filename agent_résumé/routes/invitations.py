from datetime import datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth.dependencies import AuthContext, require_organization_admin
from auth.organization_access import lock_organization
from database import get_db
from models import OrganizationInvitation, OrganizationMember, User
from notification_service import (
    mark_invitation_notifications_read,
    schedule_invitation_notifications,
)
from schema import InvitationCreate, InvitationCreated, InvitationRead, InvitationsPage


router = APIRouter(prefix="/organization/invitations", tags=["organization"])


def check_invited_role(actor: OrganizationMember, role: str) -> None:
    if actor.role == "admin" and not actor.organization.allow_admin_invitations:
        raise HTTPException(
            403,
            "Le proprietaire a desactive les invitations pour les administrateurs.",
        )
    if role == "admin" and actor.role != "owner":
        raise HTTPException(
            403,
            "Seul le proprietaire peut gerer les invitations admin.",
        )


def ensure_not_already_member(
    db: Session,
    organization_id: int,
    email: str,
) -> None:
    existing_member = (
        db.query(OrganizationMember)
        .join(User, User.id == OrganizationMember.user_id)
        .filter(
            OrganizationMember.organization_id == organization_id,
            func.lower(User.email) == email,
        )
        .first()
    )
    if existing_member is not None:
        raise HTTPException(
            409,
            "Cet utilisateur est deja membre, actif ou inactif.",
        )


def create_invitation_record(
    db: Session,
    *,
    actor: OrganizationMember,
    email: str,
    role: str,
    invited_by_user_id: int,
    now: datetime,
) -> tuple[OrganizationInvitation, str]:
    token = token_urlsafe(32)
    invitation = OrganizationInvitation(
        organization_id=actor.organization_id,
        email=email,
        role=role,
        token_hash=sha256(token.encode("utf-8")).hexdigest(),
        invited_by_user_id=invited_by_user_id,
        status="pending",
        expires_at=now
        + timedelta(days=actor.organization.invitation_expiration_days),
    )
    db.add(invitation)
    db.flush()
    schedule_invitation_notifications(
        db,
        actor.organization,
        invitation,
    )
    return invitation, token


@router.post("", response_model=InvitationCreated, status_code=201)
def create_invitation(
    payload: InvitationCreate,
    response: Response,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_organization_admin),
):
    try:
        actor = lock_organization(db, auth)
        check_invited_role(actor, payload.role)
        now = datetime.utcnow()
        ensure_not_already_member(
            db,
            actor.organization_id,
            payload.email,
        )

        existing_invitation = (
            db.query(OrganizationInvitation)
            .filter(
                OrganizationInvitation.organization_id
                == actor.organization_id,
                func.lower(OrganizationInvitation.email) == payload.email,
                OrganizationInvitation.status == "pending",
                OrganizationInvitation.expires_at > now,
            )
            .first()
        )
        if existing_invitation is not None:
            raise HTTPException(
                409,
                "Une invitation valide existe deja pour cet e-mail.",
            )

        invitation, token = create_invitation_record(
            db,
            actor=actor,
            email=payload.email,
            role=payload.role,
            invited_by_user_id=auth.user.id,
            now=now,
        )
        result = InvitationCreated(
            invitation=InvitationRead.model_validate(invitation),
            token=token,
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409,
            "Conflit lors de la creation de l'invitation.",
        )
    except Exception:
        db.rollback()
        raise

    response.headers["Cache-Control"] = "no-store"
    return result


@router.get("", response_model=InvitationsPage)
def list_invitations(
    response: Response,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_organization_admin),
):
    query = db.query(OrganizationInvitation).filter(
        OrganizationInvitation.organization_id
        == auth.membership.organization_id
    )
    total = query.count()
    items = (
        query.order_by(OrganizationInvitation.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    response.headers["Cache-Control"] = "no-store"
    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.post(
    "/{invitation_id}/renew",
    response_model=InvitationCreated,
    status_code=201,
)
def renew_invitation(
    invitation_id: int,
    response: Response,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_organization_admin),
):
    try:
        actor = lock_organization(db, auth)
        invitation = (
            db.query(OrganizationInvitation)
            .filter(
                OrganizationInvitation.id == invitation_id,
                OrganizationInvitation.organization_id
                == actor.organization_id,
            )
            .with_for_update()
            .populate_existing()
            .first()
        )
        if invitation is None:
            raise HTTPException(404, "Invitation introuvable.")

        check_invited_role(actor, invitation.role)
        now = datetime.utcnow()
        if (
            invitation.status != "pending"
            or invitation.expires_at > now
        ):
            raise HTTPException(
                409,
                "Seule une invitation expiree peut etre renouvelee.",
            )

        ensure_not_already_member(
            db,
            actor.organization_id,
            invitation.email,
        )
        invitation.status = "revoked"
        invitation.revoked_at = now
        mark_invitation_notifications_read(
            db,
            actor.organization_id,
            invitation.id,
        )

        renewed, token = create_invitation_record(
            db,
            actor=actor,
            email=invitation.email,
            role=invitation.role,
            invited_by_user_id=auth.user.id,
            now=now,
        )
        result = InvitationCreated(
            invitation=InvitationRead.model_validate(renewed),
            token=token,
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409,
            "Conflit lors du renouvellement de l'invitation.",
        )
    except Exception:
        db.rollback()
        raise

    response.headers["Cache-Control"] = "no-store"
    return result


@router.post("/{invitation_id}/revoke", response_model=InvitationRead)
def revoke_invitation(
    invitation_id: int,
    response: Response,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_organization_admin),
):
    try:
        actor = lock_organization(db, auth)
        invitation = (
            db.query(OrganizationInvitation)
            .filter(
                OrganizationInvitation.id == invitation_id,
                OrganizationInvitation.organization_id
                == actor.organization_id,
            )
            .with_for_update()
            .populate_existing()
            .first()
        )
        if invitation is None:
            raise HTTPException(404, "Invitation introuvable.")

        if invitation.role == "admin" and actor.role != "owner":
            raise HTTPException(
                403,
                "Seul le proprietaire peut gerer les invitations admin.",
            )
        if invitation.status not in ("pending", "revoked"):
            raise HTTPException(
                409,
                "Cette invitation a deja ete traitee.",
            )

        if invitation.status == "pending":
            invitation.status = "revoked"
            invitation.revoked_at = datetime.utcnow()
            mark_invitation_notifications_read(
                db,
                actor.organization_id,
                invitation.id,
            )
            db.flush()

        result = InvitationRead.model_validate(invitation)
        db.commit()
    except Exception:
        db.rollback()
        raise

    response.headers["Cache-Control"] = "no-store"
    return result
