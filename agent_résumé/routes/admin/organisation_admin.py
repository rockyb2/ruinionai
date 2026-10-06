from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import delete, func
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Meeting, Organization, OrganizationMember, User
from routes.admin.common import commit, get_record, page
from routes.admin.schemas import MembershipInput, OrganizationCreate, OrganizationUpdate

router = APIRouter(prefix="/organizations")


def organization_data(db, org):
    # Comptages séparés pour ne pas multiplier membres et réunions avec une jointure.
    members = db.query(func.count(OrganizationMember.id)).filter_by(organization_id=org.id).scalar()
    meetings, seconds = db.query(func.count(Meeting.id), func.coalesce(func.sum(Meeting.audio_duration), 0)).filter_by(organization_id=org.id).one()
    return {"id": org.id, "name": org.name, "description": org.description or "",
            "created_at": org.created_at, "updated_at": org.updated_at,
            "invitation_expiration_days": org.invitation_expiration_days,
            "allow_admin_invitations": org.allow_admin_invitations,
            "invitation_notifications_enabled": org.invitation_notifications_enabled,
            "members_count": members, "meetings_count": meetings, "audio_seconds": seconds}


@router.get("")
def list_organizations(q: str = Query("", max_length=150), offset: int = Query(0, ge=0),
                       limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    query = db.query(Organization)
    if q.strip():
        query = query.filter(Organization.name.icontains(q.strip(), autoescape=True))
    result = page(query.order_by(Organization.id.desc()), offset, limit, lambda org: organization_data(db, org))
    result["stats"] = {"organizations": db.query(Organization).count(), "members": db.query(OrganizationMember).count(),
                       "meetings": db.query(Meeting).count(),
                       "audio_seconds": db.query(func.coalesce(func.sum(Meeting.audio_duration), 0)).scalar()}
    return result


@router.post("", status_code=201)
def create_organization(payload: OrganizationCreate, db: Session = Depends(get_db)):
    owner = get_record(db, User, payload.owner_user_id, lock=True)
    if not owner.is_active:
        raise HTTPException(409, "Le propriétaire doit être un utilisateur actif.")
    org = Organization(name=payload.name, description=payload.description)
    org.members.append(OrganizationMember(user_id=owner.id, role="owner", status="active"))
    db.add(org)
    commit(db)
    return organization_data(db, org)


@router.get("/{organization_id}")
def read_organization(organization_id: int, db: Session = Depends(get_db)):
    return organization_data(db, get_record(db, Organization, organization_id))


@router.patch("/{organization_id}")
def update_organization(organization_id: int, payload: OrganizationUpdate, db: Session = Depends(get_db)):
    org = get_record(db, Organization, organization_id, lock=True)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(org, key, value)
    commit(db)
    return organization_data(db, org)


@router.delete("/{organization_id}", status_code=204)
def delete_organization(organization_id: int, db: Session = Depends(get_db)):
    get_record(db, Organization, organization_id, lock=True)
    if db.query(Meeting.id).filter_by(organization_id=organization_id).first():
        raise HTTPException(409, "Supprimez d’abord les réunions de cette organisation pour conserver le contrôle de leurs fichiers.")
    # Les clés étrangères CASCADE suppriment adhésions/invitations/notifications,
    # sans supprimer les comptes utilisateurs.
    db.execute(delete(Organization).where(Organization.id == organization_id))
    commit(db)
    return Response(status_code=204)


def member_data(member):
    user = member.user
    return {"id": member.id, "user_id": user.id, "organization_id": member.organization_id,
            "name": " ".join(filter(None, [user.first_name, user.last_name])), "email": user.email,
            "role": member.role, "status": member.status, "is_active": user.is_active}


@router.get("/{organization_id}/members")
def members(organization_id: int, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    get_record(db, Organization, organization_id)
    query = db.query(OrganizationMember).options(joinedload(OrganizationMember.user)).filter_by(organization_id=organization_id)
    return page(query.order_by(OrganizationMember.id), offset, limit, member_data)


def ensure_other_owner(db, member):
    if member.role != "owner" or member.status != "active":
        return
    other = db.query(OrganizationMember.id).join(User).filter(
        OrganizationMember.organization_id == member.organization_id, OrganizationMember.id != member.id,
        OrganizationMember.role == "owner", OrganizationMember.status == "active", User.is_active.is_(True),
    ).first()
    if other is None:
        raise HTTPException(409, "Ajoutez d’abord un autre propriétaire actif à cette organisation.")


@router.put("/{organization_id}/members/{user_id}")
def save_member(organization_id: int, user_id: int, payload: MembershipInput, db: Session = Depends(get_db)):
    if payload.user_id != user_id:
        raise HTTPException(422, "L’utilisateur ne correspond pas à l’adresse demandée.")
    get_record(db, Organization, organization_id, lock=True)
    user = get_record(db, User, user_id, lock=True)
    if payload.status == "active" and not user.is_active:
        raise HTTPException(409, "Réactivez d’abord le compte utilisateur.")
    member = db.query(OrganizationMember).filter_by(organization_id=organization_id, user_id=user_id).first()
    if member:
        if payload.role != "owner" or payload.status != "active":
            ensure_other_owner(db, member)
        member.role, member.status = payload.role, payload.status
    else:
        member = OrganizationMember(organization_id=organization_id, user_id=user_id, role=payload.role, status=payload.status)
        db.add(member)
    commit(db)
    return member_data(member)


@router.delete("/{organization_id}/members/{user_id}", status_code=204)
def delete_member(organization_id: int, user_id: int, db: Session = Depends(get_db)):
    get_record(db, Organization, organization_id, lock=True)
    member = db.query(OrganizationMember).filter_by(organization_id=organization_id, user_id=user_id).first()
    if member is None:
        raise HTTPException(404, "Membre introuvable.")
    ensure_other_owner(db, member)
    db.execute(delete(OrganizationMember).where(OrganizationMember.id == member.id))
    commit(db)
    return Response(status_code=204)
