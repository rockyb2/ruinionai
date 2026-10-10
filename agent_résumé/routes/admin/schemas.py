from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, PositiveInt, field_validator, model_validator

Name = Annotated[str, Field(min_length=1, max_length=150)]


class AdminInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @model_validator(mode="before")
    @classmethod
    def reject_null(cls, values):
        # PATCH : omettre un champ conserve sa valeur ; null ne doit pas
        # contourner les contraintes NOT NULL de la base.
        if isinstance(values, dict) and any(v is None for v in values.values()):
            raise ValueError("Omettez les champs inchangés ; les valeurs nulles ne sont pas acceptées.")
        return values


class OrganizationCreate(AdminInput):
    name: Name
    description: str = Field(default="", max_length=500)
    owner_user_id: PositiveInt


class OrganizationUpdate(AdminInput):
    name: Name | None = None
    description: str | None = Field(default=None, max_length=500)
    invitation_expiration_days: int | None = Field(default=None, ge=1, le=30)
    allow_admin_invitations: bool | None = None
    invitation_notifications_enabled: bool | None = None


class UserCreate(AdminInput):
    first_name: Name
    last_name: Name
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_bytes(cls, value):
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Le mot de passe doit contenir au plus 72 octets UTF-8.")
        return value


class UserUpdate(AdminInput):
    first_name: Name | None = None
    last_name: Name | None = None
    email: EmailStr | None = None
    is_active: bool | None = None


class PasswordUpdate(AdminInput):
    password: str = Field(min_length=8, max_length=72)
    _validate_password = field_validator("password")(UserCreate.password_bytes.__func__)


class MembershipInput(AdminInput):
    user_id: PositiveInt
    role: Literal["owner", "admin", "member"] = "member"
    status: Literal["active", "inactive"] = "active"


class MeetingCreate(AdminInput):
    organization_id: PositiveInt
    title: str = Field(min_length=1, max_length=250)


class MeetingUpdate(AdminInput):
    title: str | None = Field(default=None, min_length=1, max_length=250)
    date: datetime | None = None
