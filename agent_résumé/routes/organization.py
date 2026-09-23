from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from auth.dependencies import (
    AuthContext,
    get_auth_context,
    require_organization_admin,
    require_organization_owner,
)
from auth.organization_access import lock_organization
from database import get_db
from models import Organization, OrganizationMember
from schema import (
    OrganizationMemberDetails,
    OrganizationMemberRoleUpdate,
    OrganizationMembersPage,
    OrganizationMemberStatusUpdate,
    OrganizationSettingsRead,
    OrganizationSettingsUpdate,
)


router = APIRouter(prefix="/organization", tags=["organization"])


@router.get("/members", response_model=OrganizationMembersPage)
def list_members(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(require_organization_admin),
):
    query = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id
        == auth_context.membership.organization_id
    )

    total = query.count()

    members = (
        query.options(joinedload(OrganizationMember.user))
        .order_by(OrganizationMember.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "items": members,
        "total": total,
        "offset": offset,
        "limit": limit,
    }


def get_editable_member(
    db: Session,
    organization_id: int,
    member_id: int,
    actor: OrganizationMember,
) -> OrganizationMember:
    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == organization_id,
        )
        .with_for_update()
        .populate_existing()
        .first()
    )
    if member is None:
        raise HTTPException(404, "Membre introuvable.")
    if member.id == actor.id:
        raise HTTPException(403, "Vous ne pouvez pas modifier votre propre acces.")
    if member.role == "owner":
        raise HTTPException(403, "Le proprietaire ne peut pas etre modifie par cette API.")

    return member


@router.patch("/members/{member_id}/role", response_model=OrganizationMemberDetails)
def update_member_role(
    payload: OrganizationMemberRoleUpdate,
    response: Response,
    member_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_organization_owner),
):
    try:
        actor = lock_organization(db, auth)
        if actor.role != "owner":
            raise HTTPException(403, "Droits proprietaire requis.")

        member = get_editable_member(db, actor.organization_id, member_id, actor)
        member.role = payload.role
        db.flush()

        result = OrganizationMemberDetails.model_validate(member)
        db.commit()
    except Exception:
        db.rollback()
        raise

    response.headers["Cache-Control"] = "no-store"
    return result


@router.patch("/members/{member_id}/status", response_model=OrganizationMemberDetails)
def update_member_status(
    payload: OrganizationMemberStatusUpdate,
    response: Response,
    member_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_organization_admin),
):
    try:
        actor = lock_organization(db, auth)
        member = get_editable_member(db, actor.organization_id, member_id, actor)

        if actor.role == "admin" and member.role != "member":
            raise HTTPException(403, "Un administrateur peut gerer uniquement les membres simples.")

        member.status = payload.status
        db.flush()

        result = OrganizationMemberDetails.model_validate(member)
        db.commit()
    except Exception:
        db.rollback()
        raise

    response.headers["Cache-Control"] = "no-store"
    return result


@router.get("/settings", response_model=OrganizationSettingsRead)
def get_organization_settings(
    response: Response,
    auth: AuthContext = Depends(get_auth_context),
):
    response.headers["Cache-Control"] = "no-store"
    return auth.membership.organization


@router.patch("/settings", response_model=OrganizationSettingsRead)
def update_organization_settings(
    payload: OrganizationSettingsUpdate,
    response: Response,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_organization_owner),
):
    try:
        actor = lock_organization(db, auth)
        if actor.role != "owner":
            raise HTTPException(403, "Droits proprietaire requis.")

        organization = (
            db.query(Organization)
            .filter(Organization.id == actor.organization_id)
            .populate_existing()
            .first()
        )
        if organization is None:
            raise HTTPException(404, "Organisation introuvable.")

        changes = payload.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(organization, field, value)

        db.flush()
        result = OrganizationSettingsRead.model_validate(organization)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Ce nom d'organisation est deja utilise.")
    except Exception:
        db.rollback()
        raise

    response.headers["Cache-Control"] = "no-store"
    return result
