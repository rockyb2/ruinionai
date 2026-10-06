from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from auth.security import ALGORITHM, SECRET_KEY
from database import get_db
from models import OrganizationMember, User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@dataclass(frozen=True)
class AuthContext:
    user: User
    membership: OrganizationMember


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub", ""))
    except (JWTError, ValueError):
        raise credentials_error

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_error

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Ce compte utilisateur est inactif.")

    return user


def require_platform_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Droits de super administrateur requis.",
        )

    return current_user


def get_auth_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    organization_id: int | None = Header(
        default=None,
        alias="X-Organization-Id",
        gt=0,
    ),
) -> AuthContext:
    query = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.status == "active",
    )

    if organization_id is not None:
        query = query.filter(
            OrganizationMember.organization_id == organization_id
        )

    memberships = query.limit(2).all()

    if not memberships:
        raise HTTPException(
            status_code=403,
            detail="Aucun acces actif a cette organisation.",
        )

    if len(memberships) > 1:
        raise HTTPException(
            status_code=400,
            detail="Precisez l'organisation avec X-Organization-Id.",
        )

    return AuthContext(
        user=current_user,
        membership=memberships[0],
    )


def require_organization_admin(
    auth_context: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    if auth_context.membership.role not in ("owner", "admin"):
        raise HTTPException(
            status_code=403,
            detail="Droits administrateur requis.",
        )

    return auth_context


def require_organization_owner(
    auth_context: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    if auth_context.membership.role != "owner":
        raise HTTPException(
            status_code=403,
            detail="Droits proprietaire requis.",
        )

    return auth_context
