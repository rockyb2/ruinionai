from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import delete, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from auth.dependencies import require_platform_admin
from auth.security import hash_password
from database import get_db
from models import Meeting, Organization, OrganizationMember, User
from routes.admin.common import commit, get_record, page
from routes.admin.organisation_admin import ensure_other_owner
from routes.admin.schemas import PasswordUpdate, UserCreate, UserUpdate

router = APIRouter(prefix="/users")


def user_data(db, user):
    return {"id": user.id, "first_name": user.first_name or "", "last_name": user.last_name or "",
            "name": " ".join(filter(None, [user.first_name, user.last_name])), "email": user.email,
            "is_active": bool(user.is_active), "is_super_admin": user.is_super_admin,
            "created_at": user.created_at, "updated_at": user.updated_at,
            "meetings_count": db.query(Meeting.id).filter_by(created_by_user_id=user.id).count(),
            "memberships": [{"id": m.id, "organization_id": m.organization_id, "organization_name": m.organization.name,
                             "role": m.role, "status": m.status} for m in user.memberships]}


@router.get("")
def list_users(q: str = Query("", max_length=150), organization_id: int | None = Query(None, gt=0),
               is_active: bool | None = None, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
               db: Session = Depends(get_db)):
    query = db.query(User).options(selectinload(User.memberships).joinedload(OrganizationMember.organization))
    if q.strip():
        query = query.filter(or_(*(column.icontains(q.strip(), autoescape=True) for column in [User.first_name, User.last_name, User.email])))
    if organization_id:
        query = query.filter(User.memberships.any(OrganizationMember.organization_id == organization_id))
    if is_active is not None:
        query = query.filter(User.is_active.is_(is_active))
    result = page(query.order_by(User.id.desc()), offset, limit, lambda user: user_data(db, user))
    result["stats"] = {"total": db.query(User).count(), "active": db.query(User).filter(User.is_active.is_(True)).count(),
                       "inactive": db.query(User).filter(User.is_active.is_(False)).count(),
                       "super_admins": db.query(User).filter(User.is_super_admin.is_(True)).count()}
    return result


@router.post("", status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = User(first_name=payload.first_name, last_name=payload.last_name, email=str(payload.email).lower(),
                password_hash=hash_password(payload.password), is_active=True, is_super_admin=False)
    db.add(user)
    commit(db)
    return user_data(db, user)


@router.get("/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    return user_data(db, get_record(db, User, user_id))


def lock_user_organizations(db, user_id):
    # Même verrou d'organisation que les routes d'équipe. Ordre déterministe
    # pour préserver le dernier propriétaire lors de modifications simultanées.
    ids = db.query(OrganizationMember.organization_id).filter_by(user_id=user_id)
    db.query(Organization).filter(Organization.id.in_(ids)).order_by(Organization.id).with_for_update().all()
    return get_record(db, User, user_id, lock=True)


def protect_account(db, user, actor):
    if user.id == actor.id:
        raise HTTPException(409, "Vous ne pouvez pas désactiver ou supprimer votre propre compte.")
    if user.is_super_admin:
        raise HTTPException(409, "La désactivation d’un super administrateur n’est pas disponible dans cette interface.")
    for membership in user.memberships:
        ensure_other_owner(db, membership)


@router.patch("/{user_id}")
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), actor: User = Depends(require_platform_admin)):
    user = lock_user_organizations(db, user_id)
    values = payload.model_dump(exclude_unset=True)
    if values.get("is_active") is False:
        protect_account(db, user, actor)
    if "email" in values:
        values["email"] = str(values["email"]).lower()
    for key, value in values.items():
        setattr(user, key, value)
    commit(db)
    return user_data(db, user)


@router.post("/{user_id}/password", status_code=204)
def reset_password(user_id: int, payload: PasswordUpdate, db: Session = Depends(get_db)):
    user = get_record(db, User, user_id, lock=True)
    user.password_hash = hash_password(payload.password)
    commit(db)
    return Response(status_code=204)


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db), actor: User = Depends(require_platform_admin)):
    user = lock_user_organizations(db, user_id)
    protect_account(db, user, actor)
    # SET NULL conserve les réunions créées ; CASCADE retire les adhésions.
    db.execute(delete(User).where(User.id == user.id))
    commit(db)
    return Response(status_code=204)
