from database import Base
from sqlalchemy import Column, Integer, String, Text, DateTime,ForeignKey,Boolean,Enum
from sqlalchemy import CheckConstraint, UniqueConstraint, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime





# organisation Saas

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_active = Column(Boolean, default=True)
    is_super_admin = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    memberships = relationship(
        "OrganizationMember",
        back_populates="user",
    )
    meetings = relationship(
        "Meeting",
        back_populates="created_by",
    )
    sent_invitations = relationship(
        "OrganizationInvitation",
        back_populates="invited_by",
    )
    notifications = relationship(
        "OrganizationNotification",
        back_populates="user",
        passive_deletes=True,
    )

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    description = Column(Text, nullable=True)
    invitation_expiration_days = Column(
        Integer,
        nullable=False,
        default=7,
        server_default="7",
    )
    allow_admin_invitations = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    invitation_notifications_enabled = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    __table_args__ = (
        CheckConstraint(
            "invitation_expiration_days BETWEEN 1 AND 30",
            name="ck_organizations_invitation_expiration_days",
        ),
    )

    members = relationship("OrganizationMember", back_populates="organization")
    meetings = relationship("Meeting", back_populates="organization")
    invitations = relationship("OrganizationInvitation", back_populates="organization")
    notifications = relationship(
        "OrganizationNotification",
        back_populates="organization",
        passive_deletes=True,
    )


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "user_id",
            name="uq_organization_members_organization_user",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(
        Enum(
            "owner",
            "admin",
            "member",
            name="organization_member_role",
        ),
        nullable=False,
        default="member",
        server_default="member",
    )
    status = Column(
        Enum(
            "active",
            "inactive",
            name="organization_member_status",
        ),
        nullable=False,
        default="active",
        server_default="active",
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="memberships")


class OrganizationInvitation(Base):
    __tablename__ = "organization_invitations"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    email = Column(
        String(255),
        nullable=False,
        index=True,
    )

    role = Column(
        Enum(
            "admin",
            "member",
            name="organization_invitation_role",
        ),
        nullable=False,
        default="member",
        server_default="member",
    )

    # Empreinte SHA-256 du jeton aléatoire envoyé dans l'invitation.
    token_hash = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    invited_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    status = Column(
        Enum(
            "pending",
            "accepted",
            "declined",
            "revoked",
            name="organization_invitation_status",
        ),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Date limite obligatoire, calculée lors de la création.
    # Les dates suivent la convention UTC du projet.
    expires_at = Column(DateTime, nullable=False)

    accepted_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    organization = relationship(
        "Organization",
        back_populates="invitations",
    )

    invited_by = relationship(
        "User",
        back_populates="sent_invitations",
    )

    notifications = relationship(
        "OrganizationNotification",
        back_populates="invitation",
        passive_deletes=True,
    )


class OrganizationNotification(Base):
    __tablename__ = "organization_notifications"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "kind",
            "invitation_id",
            name="uq_organization_notifications_user_kind_invitation",
        ),
        UniqueConstraint(
            "user_id", "kind", "meeting_id",
            name="uq_organization_notifications_user_kind_meeting",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invitation_id = Column(
        Integer,
        ForeignKey("organization_invitations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    kind = Column(String(40), nullable=False)
    meeting_id = Column(
        Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=True, index=True,
    )
    title = Column(String(180), nullable=False)
    message = Column(String(500), nullable=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="notifications")
    user = relationship("User", back_populates="notifications")
    invitation = relationship(
        "OrganizationInvitation",
        back_populates="notifications",
    )


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String, index=True)
    transcription = Column(Text)
    date = Column(DateTime, default=datetime.utcnow)
    participants = Column(Text, nullable=True)
    summary_short = Column(Text, nullable=True)
    summary_long = Column(Text, nullable=True)
    report_path = Column(String, nullable=True)
    audio_manifest = Column(JSON, nullable=True)
    audio_path = Column(String, nullable=True)
    audio_duration = Column(Float, nullable=True)
    transcription_segments = Column(JSON, nullable=True)
    processing_status = Column(String(24), nullable=False, default="idle", server_default="idle", index=True)
    processing_error = Column(Text, nullable=True)
    processing_token = Column(String(36), nullable=True)
    processing_expires_at = Column(DateTime, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="meetings")
    created_by = relationship("User", back_populates="meetings")
    invited_members = relationship(
        "MeetingParticipant", cascade="all, delete-orphan", lazy="selectin",
        order_by="MeetingParticipant.id", passive_deletes=True,
    )

    @property
    def audio_available(self):
        return bool(self.audio_path)

    @property
    def has_source_audio(self):
        return bool(self.audio_manifest or self.audio_path)

    @property
    def participant_member_ids(self):
        return [participant.member_id for participant in self.invited_members]

    @property
    def summary(self):
        return self.summary_long

    @summary.setter
    def summary(self, value):
        self.summary_long = value


class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"
    __table_args__ = (
        UniqueConstraint("meeting_id", "member_id", name="uq_meeting_participants_meeting_member"),
    )

    id = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("organization_members.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
