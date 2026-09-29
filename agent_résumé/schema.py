from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    PositiveInt,
    computed_field,
    field_validator,
)
from typing import List, Literal, Optional
from datetime import datetime


OrganizationRole = Literal["owner", "admin", "member"]
AssignableOrganizationRole = Literal["admin", "member"]
OrganizationMemberStatus = Literal["active", "inactive"]


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


class OrganizationSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    invitation_expiration_days: int
    allow_admin_invitations: bool
    invitation_notifications_enabled: bool
    updated_at: Optional[datetime] = None


class OrganizationSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    description: Optional[str] = Field(default=None, max_length=500)
    invitation_expiration_days: Optional[int] = Field(default=None, ge=1, le=30)
    allow_admin_invitations: Optional[bool] = None
    invitation_notifications_enabled: Optional[bool] = None

    @field_validator("name", "description", mode="before")
    @classmethod
    def trim_organization_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class OrganizationMemberCreate(BaseModel):
    organization_id: int
    user_id: int
    role: AssignableOrganizationRole = "member"


class OrganizationMemberRoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: AssignableOrganizationRole


class OrganizationMemberStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: OrganizationMemberStatus


class OrganizationMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    user_id: int
    role: OrganizationRole
    status: OrganizationMemberStatus
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class OrganizationMemberDetails(OrganizationMemberRead):
    user: UserRead


class OrganizationMembersPage(BaseModel):
    items: List[OrganizationMemberDetails]
    total: int
    offset: int
    limit: int


InvitationStatus = Literal["pending", "accepted", "declined", "revoked"]


class InvitationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(max_length=255)
    role: AssignableOrganizationRole = "member"

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class InvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    email: str
    role: AssignableOrganizationRole
    status: InvitationStatus
    invited_by_user_id: Optional[int]
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime]
    revoked_at: Optional[datetime]

    @computed_field
    @property
    def is_expired(self) -> bool:
        return self.status == "pending" and self.expires_at <= datetime.utcnow()


class InvitationCreated(BaseModel):
    invitation: InvitationRead
    token: str


class InvitationsPage(BaseModel):
    items: List[InvitationRead]
    total: int
    offset: int
    limit: int


NotificationKind = Literal[
    "invitation_expiring",
    "invitation_expired",
    "invitation_accepted",
    "meeting_invitation",
]


class OrganizationNotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    invitation_id: Optional[int] = None
    meeting_id: Optional[int] = None
    kind: NotificationKind
    title: str
    message: str
    read_at: Optional[datetime] = None
    created_at: datetime

    @computed_field
    @property
    def is_read(self) -> bool:
        return self.read_at is not None


class OrganizationNotificationsPage(BaseModel):
    items: List[OrganizationNotificationRead]
    total: int
    unread_count: int
    offset: int
    limit: int


class NotificationSyncRead(BaseModel):
    created: int


class InvitationAccept(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=32, max_length=256)


class InvitationRegister(InvitationAccept):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def trim_name(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Le mot de passe depasse la limite de 72 octets de bcrypt.")
        return value


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
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=250)
    participant_member_ids: List[PositiveInt] = Field(default_factory=list, max_length=100)

    @field_validator("title", mode="before")
    @classmethod
    def trim_title(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("participant_member_ids")
    @classmethod
    def unique_members(cls, value):
        return list(dict.fromkeys(value))


class MeetingInviteeRead(BaseModel):
    member_id: int
    name: str
    email: str


class MeetingInviteesPage(BaseModel):
    items: List[MeetingInviteeRead]
    total: int
    offset: int
    limit: int


class TranscriptSegment(BaseModel):
    start: float = Field(ge=0, allow_inf_nan=False)
    end: float = Field(ge=0, allow_inf_nan=False)
    text: str


class MeetingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: Optional[int] = None
    created_by_user_id: Optional[int] = None
    title: str
    transcription: Optional[str] = None
    participants: Optional[str] = None
    participant_member_ids: List[int] = Field(default_factory=list)
    summary: Optional[str] = None
    summary_short: Optional[str] = None
    summary_long: Optional[str] = None
    report_path: Optional[str] = None
    audio_available: bool = False
    has_source_audio: bool = False
    audio_duration: Optional[float] = None
    transcription_segments: Optional[List[TranscriptSegment]] = None
    processing_status: str = "idle"
    processing_error: Optional[str] = None
    date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
