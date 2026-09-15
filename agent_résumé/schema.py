from pydantic import BaseModel, ConfigDict, Field
from typing import List, Literal, Optional
from datetime import datetime


OrganizationRole = Literal["admin", "member"]


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    is_active: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class OrganizationCreate(BaseModel):
    name: str


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class OrganizationMemberCreate(BaseModel):
    organization_id: int
    user_id: int
    role: OrganizationRole = "member"


class OrganizationMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    user_id: int
    role: OrganizationRole
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RegisterRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    organization_name: str = Field(..., min_length=1, max_length=150)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthResponse(Token):
    user: UserRead
    organization: OrganizationRead
    role: OrganizationRole


class CurrentUserResponse(BaseModel):
    user: UserRead
    organization: Optional[OrganizationRead] = None
    role: Optional[OrganizationRole] = None


class MeetingCreate(BaseModel):
    title: str
    participants: Optional[List[str]] = None


class MeetingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: Optional[int] = None
    created_by_user_id: Optional[int] = None
    title: str
    transcription: Optional[str] = None
    participants: Optional[str] = None
    summary: Optional[str] = None
    summary_short: Optional[str] = None
    summary_long: Optional[str] = None
    report_path: Optional[str] = None
    date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
