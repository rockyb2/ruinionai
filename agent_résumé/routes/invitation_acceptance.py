from datetime import datetime
from hashlib import sha256

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from auth.security import create_access_token, hash_password
from database import get_db
from models import Organization, OrganizationInvitation, OrganizationMember, User
from notification_service import (
    notify_invitation_accepted,
    sync_invitation_notifications_for_user,
)
from schema import (
    AuthResponse,
    InvitationAccept,
    InvitationRegister,
    OrganizationRead,
    UserRead,
)


router = APIRouter(prefix="/invitations", tags=["invitations"])


def lock_invitation(db: Session, token: str):
    token_hash = sha256(token.encode("utf-8")).hexdigest()
    organization_id = (
        db.query(OrganizationInvitation.organization_id)
        .filter(OrganizationInvitation.token_hash == token_hash)
        .scalar()
    )
    if organization_id is None:
        raise HTTPException(404, "Invitation introuvable.")

    # Meme ordre de verrouillage que la creation et la revocation.
    organization = (
        db.query(Organization)
        .filter(Organization.id == organization_id)
        .with_for_update()
        .populate_existing()
        .first()
    )
    if organization is None:
        raise HTTPException(404, "Invitation introuvable.")

    invitation = (
        db.query(OrganizationInvitation)
        .filter(
            OrganizationInvitation.token_hash == token_hash,
            OrganizationInvitation.organization_id == organization_id,
        )
        .with_for_update()
        .populate_existing()
        .first()
    )
    if invitation is None:
        raise HTTPException(404, "Invitation introuvable.")
    if invitation.status != "pending":
        raise HTTPException(409, "Cette invitation n'est plus utilisable.")
    if invitation.expires_at <= datetime.utcnow():
        raise HTTPException(410, "Cette invitation a expire.")

    return organization, invitation


def join_organization(db, organization, invitation, user) -> AuthResponse:
    membership = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization.id,
            OrganizationMember.user_id == user.id,
        )
        .first()
    )
    if membership is not None:
        raise HTTPException(409, "Vous etes deja membre, actif ou inactif.")

    now = datetime.utcnow()
    if invitation.expires_at <= now:
        raise HTTPException(410, "Cette invitation a expire.")

    membership = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role=invitation.role,
        status="active",
    )
    db.add(membership)
    invitation.status = "accepted"
    invitation.accepted_at = now
    db.flush()

    notify_invitation_accepted(
        db,
        organization,
        invitation,
        exclude_user_id=user.id,
    )
    if membership.role == "admin":
        sync_invitation_notifications_for_user(
            db,
            organization,
            user.id,
        )
    db.flush()

    # Preparer la reponse avant le commit.
    return AuthResponse(
        access_token=create_access_token(subject=str(user.id)),
        user=UserRead.model_validate(user),
        organization=OrganizationRead.model_validate(organization),
        role=membership.role,
    )


@router.post("/accept", response_model=AuthResponse)
def accept_invitation(
    payload: InvitationAccept,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        organization, invitation = lock_invitation(db, payload.token)
        db.refresh(current_user)

        if not current_user.is_active:
            raise HTTPException(403, "Compte desactive.")
        if current_user.email.strip().lower() != invitation.email:
            raise HTTPException(403, "Cette invitation concerne une autre adresse e-mail.")

        result = join_organization(db, organization, invitation, current_user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Impossible de rejoindre cette organisation.")
    except Exception:
        db.rollback()
        raise

    response.headers["Cache-Control"] = "no-store"
    return result


@router.post("/register", response_model=AuthResponse, status_code=201)
def register_from_invitation(
    payload: InvitationRegister,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        organization, invitation = lock_invitation(db, payload.token)
        existing_user = (
            db.query(User)
            .filter(func.lower(User.email) == invitation.email)
            .first()
        )
        if existing_user is not None:
            raise HTTPException(409, "Un compte existe deja. Connectez-vous pour accepter.")

        user = User(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=invitation.email,
            password_hash=hash_password(payload.password),
            is_active=True,
        )
        db.add(user)
        db.flush()

        result = join_organization(db, organization, invitation, user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Un compte ou une adhesion existe deja.")
    except Exception:
        db.rollback()
        raise

    response.headers["Cache-Control"] = "no-store"
    return result
