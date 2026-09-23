from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth.dependencies import AuthContext, get_auth_context
from auth.security import create_access_token, hash_password, verify_password
from database import get_db
from models import Organization, OrganizationMember, User
from schema import AuthResponse, CurrentUserResponse, LoginRequest, RegisterRequest, Token


router = APIRouter(prefix="/auth", tags=["auth"])


def normalize_email(email: str) -> str:
    return email.strip().lower()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = normalize_email(payload.email)
    organization_name = payload.organization_name.strip()

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    existing_organization = (
        db.query(Organization).filter(Organization.name == organization_name).first()
    )
    if existing_organization is not None:
        raise HTTPException(status_code=409, detail="Organization already exists")

    user = User(
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        is_active=True,
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
        raise HTTPException(status_code=409, detail="Account already exists")

    db.refresh(user)
    db.refresh(organization)
    db.refresh(membership)

    return {
        "access_token": create_access_token(subject=str(user.id)),
        "token_type": "bearer",
        "user": user,
        "organization": organization,
        "role": membership.role,
    }


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = normalize_email(payload.email)
    user = db.query(User).filter(User.email == email).first()

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")

    return {
        "access_token": create_access_token(subject=str(user.id)),
        "token_type": "bearer",
    }


@router.get("/me", response_model=CurrentUserResponse)
def read_current_user(auth_context: AuthContext = Depends(get_auth_context)):
    return {
        "user": auth_context.user,
        "organization": auth_context.membership.organization,
        "role": auth_context.membership.role,
    }
