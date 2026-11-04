import os
from datetime import datetime, timedelta
from hashlib import sha256

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from audit_service import add_audit_log
from auth.dependencies import AuthContext, get_current_user, get_member_organization_context
from auth.rate_limit import limiter
from auth.security import create_access_token, hash_password, verify_password
from database import get_db
from models import EmailVerificationToken, Organization, OrganizationMember, User
from schema import (
    CURRENT_TERMS_VERSION,
    CurrentUserResponse,
    EmailVerificationRequest,
    EmailVerificationResponse,
    LoginRequest,
    ONBOARDING_VERSION,
    OnboardingStateRead,
    OnboardingStateUpdate,
    RegisterRequest,
    RegistrationPendingResponse,
    ResendEmailVerificationRequest,
    Token,
)
from services.email_verification_service import (
    create_email_verification_token,
    deliver_welcome_verification_email,
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


def onboarding_state(user: User) -> dict:
    return {
        "version": user.onboarding_version,
        "steps": user.onboarding_steps or {},
        "completed_at": user.onboarding_completed_at,
        "dismissed_at": user.onboarding_dismissed_at,
    }


@router.post(
    "/register",
    response_model=RegistrationPendingResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("3 per 3 minutes")
def register(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
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
        verification_token = create_email_verification_token(db, user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ce compte existe déjà.")

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
    background_tasks.add_task(
        deliver_welcome_verification_email,
        user.email,
        user.first_name,
        verification_token,
    )
    response.headers["Cache-Control"] = "no-store"

    return {
        "message": "Compte cree. Consultez votre e-mail pour confirmer votre adresse.",
        "email": user.email,
        "verification_required": True,
    }


@router.post("/verify-email", response_model=EmailVerificationResponse)
@limiter.limit("10/minute")
def verify_email(
    request: Request,
    response: Response,
    payload: EmailVerificationRequest,
    db: Session = Depends(get_db),
):
    token_hash = sha256(payload.token.encode("utf-8")).hexdigest()
    user_id = (
        db.query(EmailVerificationToken.user_id)
        .filter(EmailVerificationToken.token_hash == token_hash)
        .scalar()
    )
    if user_id is None:
        raise HTTPException(status_code=400, detail="Lien de verification invalide.")

    # Le meme ordre de verrouillage (utilisateur, puis jeton) est utilise par
    # la validation et le renvoi afin d'eviter les courses et interblocages.
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .with_for_update()
        .populate_existing()
        .first()
    )
    if user is None:
        raise HTTPException(status_code=400, detail="Lien de verification invalide.")

    verification = (
        db.query(EmailVerificationToken)
        .filter(
            EmailVerificationToken.token_hash == token_hash,
            EmailVerificationToken.user_id == user_id,
        )
        .with_for_update()
        .populate_existing()
        .first()
    )
    if verification is None:
        raise HTTPException(status_code=400, detail="Lien de verification invalide.")

    if verification.used_at is not None:
        if user.email_verified_at is not None:
            response.headers["Cache-Control"] = "no-store"
            return {
                "message": "Cette adresse e-mail est deja verifiee.",
                "verified": True,
            }
        raise HTTPException(status_code=400, detail="Lien de verification invalide.")

    now = datetime.utcnow()
    if verification.expires_at <= now:
        verification.used_at = now
        db.commit()
        raise HTTPException(status_code=410, detail="Ce lien de verification a expire.")

    user.email_verified_at = now
    verification.used_at = now
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id,
        EmailVerificationToken.id != verification.id,
        EmailVerificationToken.used_at.is_(None),
    ).update(
        {EmailVerificationToken.used_at: now},
        synchronize_session=False,
    )
    add_audit_log(
        db,
        action="AUTH_EMAIL_VERIFIED",
        request=request,
        actor_id=user.id,
        target_type="user",
        target_id=user.id,
        status_code=200,
    )
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return {
        "message": "Votre adresse e-mail est verifiee. Vous pouvez vous connecter.",
        "verified": True,
    }


@router.post(
    "/resend-verification",
    response_model=EmailVerificationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@limiter.limit("3 per 15 minutes")
def resend_email_verification(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    payload: ResendEmailVerificationRequest,
    db: Session = Depends(get_db),
):
    email = normalize_email(str(payload.email))
    user = (
        db.query(User)
        .filter(User.email == email)
        .with_for_update()
        .populate_existing()
        .first()
    )
    now = datetime.utcnow()

    if user is not None and user.email_verified_at is None:
        latest = (
            db.query(EmailVerificationToken)
            .filter(EmailVerificationToken.user_id == user.id)
            .order_by(EmailVerificationToken.created_at.desc())
            .first()
        )
        if latest is None or latest.created_at <= now - timedelta(minutes=2):
            token = create_email_verification_token(db, user, now=now)
            add_audit_log(
                db,
                action="AUTH_EMAIL_VERIFICATION_RESENT",
                request=request,
                actor_id=user.id,
                target_type="user",
                target_id=user.id,
                status_code=202,
            )
            db.commit()
            background_tasks.add_task(
                deliver_welcome_verification_email,
                user.email,
                user.first_name,
                token,
            )

    response.headers["Cache-Control"] = "no-store"
    return {
        "message": (
            "Si un compte non verifie correspond a cette adresse, "
            "un nouvel e-mail sera envoye."
        ),
        "verified": False,
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

    if user.email_verified_at is None:
        add_audit_log(
            db,
            action="AUTH_LOGIN_EMAIL_UNVERIFIED",
            request=request,
            actor_id=user.id,
            target_type="user",
            target_id=user.id,
            status_code=403,
        )
        db.commit()
        raise HTTPException(
            status_code=403,
            detail={
                "code": "EMAIL_NOT_VERIFIED",
                "message": "Confirmez votre adresse e-mail avant de vous connecter.",
            },
        )

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


@router.patch("/onboarding", response_model=OnboardingStateRead)
def update_onboarding(
    payload: OnboardingStateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = (
        db.query(User)
        .filter(User.id == current_user.id)
        .with_for_update()
        .populate_existing()
        .one()
    )
    now = datetime.utcnow()
    if user.onboarding_version != ONBOARDING_VERSION:
        user.onboarding_version = ONBOARDING_VERSION
        user.onboarding_steps = {}
        user.onboarding_completed_at = None
        user.onboarding_dismissed_at = None

    user.onboarding_steps = {
        **(user.onboarding_steps or {}),
        **payload.steps,
    }
    if payload.dismissed is not None:
        user.onboarding_dismissed_at = now if payload.dismissed else None
    if payload.completed is not None:
        user.onboarding_completed_at = now if payload.completed else None
    db.commit()
    db.refresh(user)
    return onboarding_state(user)


@router.post("/onboarding/reset", response_model=OnboardingStateRead)
def reset_onboarding(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = (
        db.query(User)
        .filter(User.id == current_user.id)
        .with_for_update()
        .populate_existing()
        .one()
    )
    user.onboarding_version = ONBOARDING_VERSION
    user.onboarding_steps = {}
    user.onboarding_completed_at = None
    user.onboarding_dismissed_at = None
    db.commit()
    db.refresh(user)
    return onboarding_state(user)
