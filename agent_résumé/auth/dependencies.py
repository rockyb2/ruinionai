from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session

from auth.security import decode_access_token
from database import get_db
from models import OrganizationMember, User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@dataclass(frozen=True)
class AuthContext:
    user: User
    membership: OrganizationMember


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        if payload.get("typ") != "access":
            raise jwt.InvalidTokenError("Type de jeton invalide.")
        user_id = int(payload.get("sub", ""))
        token_version = int(payload.get("ver", -1))
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise credentials_error

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_error

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Ce compte utilisateur est inactif.")

    if token_version != user.token_version:
        raise credentials_error

    request.state.current_user_id = user.id

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


def get_member_organization_context(
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
    auth_context: AuthContext = Depends(get_member_organization_context),
) -> AuthContext:
    if auth_context.membership.role not in ("owner", "admin"):
        raise HTTPException(
            status_code=403,
            detail="Droits administrateur requis.",
        )

    return auth_context


def require_organization_owner(
    auth_context: AuthContext = Depends(get_member_organization_context),
) -> AuthContext:
    if auth_context.membership.role != "owner":
        raise HTTPException(
            status_code=403,
            detail="Droits proprietaire requis.",
        )

    return auth_context
