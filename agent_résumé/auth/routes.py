import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from audit_service import add_audit_log
from auth.dependencies import AuthContext, get_current_user, get_member_organization_context
from auth.rate_limit import limiter
from auth.security import create_access_token, hash_password, verify_password
from database import get_db
from models import Organization, OrganizationMember, User
from schema import (
    CURRENT_TERMS_VERSION,
    AuthResponse,
    CurrentUserResponse,
    LoginRequest,
    RegisterRequest,
    Token,
)


router = APIRouter(prefix="/auth", tags=["auth"])
MAX_LOGIN_FAILURES = 10
LOCKOUT_MINUTES = 15
DUMMY_PASSWORD_HASH = hash_password("mot-de-passe-factice-uniquement-pour-le-timing")


def public_registration_enabled() -> bool:
    return os.getenv("PUBLIC_REGISTRATION_ENABLED", "false").strip().lower() in {
        "1", "true", "yes", "on",
    }


def normalize_email(email: str) -> str:
    return email.strip().lower()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3 per 3 minutes")
def register(
    request: Request,
    response: Response,
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    if not public_registration_enabled():
        raise HTTPException(
            status_code=403,
            detail="L'inscription publique est désactivée. Utilisez une invitation.",
        )
    email = normalize_email(payload.email)
    organization_name = payload.organization_name.strip()

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user is not None:
        raise HTTPException(status_code=409, detail="Cette adresse e-mail est déjà utilisée.")

    existing_organization = (
        db.query(Organization).filter(Organization.name == organization_name).first()
    )
    if existing_organization is not None:
        raise HTTPException(status_code=409, detail="Cette organisation existe déjà.")

    user = User(
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        is_active=True,
        accepted_terms_at=datetime.utcnow(),
        accepted_terms_version=CURRENT_TERMS_VERSION,
    )
    organization = Organization(name=organization_name)

    try:
        db.add(user)
        db.add(organization)
        db.flush()

        membership = OrganizationMember(
            user_id=user.id,
            organization_id=organization.id,
            role="owner",
            status="active",
        )
        db.add(membership)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ce compte existe déjà.")

    db.refresh(user)
    db.refresh(organization)
    db.refresh(membership)

    add_audit_log(
        db,
        action="AUTH_REGISTER_SUCCESS",
        request=request,
        actor_id=user.id,
        target_type="user",
        target_id=user.id,
        status_code=201,
    )
    db.commit()
    response.headers["Cache-Control"] = "no-store"

    return {
        "access_token": create_access_token(str(user.id), user.token_version),
        "token_type": "bearer",
        "user": user,
        "organization": organization,
        "role": membership.role,
    }


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    email = normalize_email(payload.email)
    user = db.query(User).filter(User.email == email).first()
    now = datetime.utcnow()

    if user is not None and user.locked_until and user.locked_until > now:
        add_audit_log(
            db,
            action="AUTH_LOGIN_BLOCKED",
            request=request,
            actor_id=user.id,
            target_type="user",
            target_id=user.id,
            status_code=429,
        )
        db.commit()
        raise HTTPException(
            status_code=429,
            detail="Trop de tentatives. Réessayez dans quelques minutes.",
        )

    password_hash = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
    password_valid = verify_password(payload.password, password_hash)
    if user is None or not password_valid:
        if user is not None:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_LOGIN_FAILURES:
                user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
        add_audit_log(
            db,
            action="AUTH_LOGIN_FAILED",
            request=request,
            actor_id=user.id if user else None,
            target_type="user",
            target_id=user.id if user else None,
            status_code=401,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        add_audit_log(
            db,
            action="AUTH_LOGIN_INACTIVE",
            request=request,
            actor_id=user.id,
            target_type="user",
            target_id=user.id,
            status_code=403,
        )
        db.commit()
        raise HTTPException(status_code=403, detail="Ce compte utilisateur est inactif.")

    user.failed_login_attempts = 0
    user.locked_until = None
    add_audit_log(
        db,
        action="AUTH_LOGIN_SUCCESS",
        request=request,
        actor_id=user.id,
        target_type="user",
        target_id=user.id,
        status_code=200,
    )
    db.commit()
    response.headers["Cache-Control"] = "no-store"

    return {
        "access_token": create_access_token(str(user.id), user.token_version),
        "token_type": "bearer",
    }


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.token_version += 1
    add_audit_log(
        db,
        action="AUTH_LOGOUT_ALL_SESSIONS",
        request=request,
        actor_id=current_user.id,
        target_type="user",
        target_id=current_user.id,
        status_code=204,
    )
    db.commit()
    return Response(status_code=204)


@router.get("/me", response_model=CurrentUserResponse)
def read_current_user(
    auth_context: AuthContext = Depends(get_member_organization_context),
):
    return {
        "user": auth_context.user,
        "organization": auth_context.membership.organization,
        "role": auth_context.membership.role,
    }
