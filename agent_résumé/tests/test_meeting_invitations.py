"""Real ORM + HTTP tests in an isolated database; no email or AI provider calls."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "meeting-tests-only-not-a-production-secret-key")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from auth.dependencies import get_current_user
from database import Base, get_db
from models import Meeting, MeetingParticipant, Organization, OrganizationMember, OrganizationNotification, User
from routes import meetings, notifications


class MeetingInvitationsTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        event.listen(self.engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"))
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add_all([Organization(id=1, name="Équipe"), Organization(id=2, name="Autre équipe")])
        names = [("Julie", "Martin"), ("Awa", "Koné"), ("Membre", "Inactif"), ("Compte", "Désactivé"), ("Autre", "Organisation")]
        for index, (first, last) in enumerate(names, 1):
            self.db.add(User(id=index, first_name=first, last_name=last, email=f"user{index}@example.test", is_active=index != 4))
        self.db.flush()
        for index in range(1, 6):
            self.db.add(OrganizationMember(
                id=index + 10, user_id=index, organization_id=2 if index == 5 else 1,
                role="owner" if index == 1 else "member", status="inactive" if index == 3 else "active",
            ))
        self.db.commit()
        self.current_user_id = 1
        app = FastAPI()
        app.include_router(meetings.router)
        app.include_router(notifications.router)
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_user] = lambda: self.db.get(User, self.current_user_id)
        self.client = TestClient(app, headers={"X-Organization-Id": "1"}, raise_server_exceptions=False)

    def tearDown(self):
        self.client.close()
        self.db.close()
        self.engine.dispose()

    def create_meeting(self, **kwargs):
        return self.client.post("/meetings/", json={"title": "Budget d’équipe", "participant_member_ids": [12], **kwargs})

    def notification_list(self):
        response = self.client.get("/organization/notifications")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_directory_excludes_self_other_organizations_and_inactive_members(self):
        response = self.client.get("/meetings/invitees?limit=1")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["total"], 1)
        self.assertEqual(response.json()["items"], [{"member_id": 12, "name": "Awa Koné", "email": "user2@example.test"}])
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(self.client.get("/meetings/invitees?q=AWA").json()["total"], 1)
        self.assertEqual(self.client.get("/meetings/invitees", params={"q": "Awa Koné"}).json()["total"], 1)
        self.assertEqual(self.client.get("/meetings/invitees?q=%25").json()["total"], 0)
        self.assertEqual(self.client.get("/meetings/invitees?offset=1").json()["items"], [])

    def test_invitation_is_persisted_once_and_visible_to_recipient(self):
        response = self.create_meeting(participant_member_ids=[12, 12, 11])
        self.assertEqual(response.status_code, 200, response.text)
        meeting = response.json()
        self.assertEqual(meeting["participant_member_ids"], [12])
        self.assertEqual(meeting["participants"], "Julie Martin, Awa Koné")
        self.assertEqual(self.db.query(MeetingParticipant).count(), 1)
        self.assertEqual(self.db.query(OrganizationNotification).count(), 1)
        self.assertEqual(self.notification_list()["total"], 0)

        self.current_user_id = 2
        result = self.notification_list()
        self.assertEqual(result["unread_count"], 1)
        invitation = result["items"][0]
        self.assertEqual(invitation["meeting_id"], meeting["id"])
        self.assertIn("Julie Martin", invitation["message"])
        self.assertIn("Budget d’équipe", invitation["message"])
        self.assertEqual(self.client.get(f'/meetings/{meeting["id"]}').status_code, 200)
        for _ in range(2):
            marked = self.client.patch(f'/organization/notifications/{invitation["id"]}/read')
            self.assertEqual(marked.status_code, 200, marked.text)
            self.assertTrue(marked.json()["is_read"])
        self.assertEqual(self.notification_list()["unread_count"], 0)

        self.current_user_id = 1
        self.assertEqual(self.client.patch(f'/organization/notifications/{invitation["id"]}/read').status_code, 404)
        self.current_user_id = 5
        self.client.headers["X-Organization-Id"] = "2"
        self.assertEqual(self.notification_list()["total"], 0)
        self.assertEqual(self.client.get(f'/meetings/{meeting["id"]}').status_code, 404)

    def test_invalid_invitees_reject_entire_creation(self):
        for member_id in (13, 14, 15, 999):
            with self.subTest(member_id=member_id):
                response = self.create_meeting(participant_member_ids=[12, member_id])
                self.assertEqual(response.status_code, 422, response.text)
                self.assertEqual(self.db.query(Meeting).count(), 0)
                self.assertEqual(self.db.query(OrganizationNotification).count(), 0)

    def test_ordinary_members_can_invite_active_teammates(self):
        self.current_user_id = 2
        self.assertEqual(self.client.get("/meetings/invitees").json()["items"][0]["member_id"], 11)
        response = self.create_meeting(participant_member_ids=[11])
        self.assertEqual(response.status_code, 200, response.text)
        self.current_user_id = 1
        self.assertEqual(self.notification_list()["unread_count"], 1)

    def test_meeting_notifications_are_independent_of_admin_invitation_alerts(self):
        self.create_meeting()
        organization = self.db.get(Organization, 1)
        organization.invitation_notifications_enabled = False
        legacy = OrganizationNotification(organization_id=1, user_id=2, kind="invitation_accepted", title="Admin only", message="Team invitation")
        self.db.add(legacy)
        self.db.commit()
        self.current_user_id = 2
        self.assertEqual(self.notification_list()["total"], 1)
        self.assertEqual(self.client.patch(f'/organization/notifications/{legacy.id}/read').status_code, 404)
        self.assertEqual(self.client.post('/organization/notifications/read-all').status_code, 204)
        self.assertEqual(self.notification_list()["unread_count"], 0)
        self.db.refresh(legacy)
        self.assertIsNone(legacy.read_at)
        organization.invitation_notifications_enabled = True
        self.db.commit()
        self.assertEqual(self.notification_list()["total"], 1)

    def test_admin_alerts_keep_existing_visibility(self):
        self.db.add(OrganizationNotification(organization_id=1, user_id=1, kind="invitation_accepted", title="Accepted", message="Team invitation"))
        self.db.commit()
        self.assertEqual(self.notification_list()["total"], 1)
        self.db.get(Organization, 1).invitation_notifications_enabled = False
        self.db.commit()
        self.assertEqual(self.notification_list()["total"], 0)

    def test_meeting_without_invitees_and_legacy_participants(self):
        response = self.create_meeting(participant_member_ids=[])
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.db.query(OrganizationNotification).count(), 0)
        legacy = Meeting(organization_id=1, title="Ancienne réunion", participants="Ancien participant")
        self.db.add(legacy)
        self.db.commit()
        response = self.client.get(f"/meetings/{legacy.id}")
        self.assertEqual(response.json()["participants"], "Ancien participant")
        self.assertEqual(response.json()["participant_member_ids"], [])

    def test_creation_rolls_back_notifications_and_meeting_together(self):
        with patch.object(self.db, "commit", side_effect=RuntimeError("Database unavailable")):
            self.assertEqual(self.create_meeting().status_code, 500)
        self.assertEqual(self.db.query(Meeting).count(), 0)
        self.assertEqual(self.db.query(OrganizationNotification).count(), 0)

    def test_invalid_payloads_and_unauthorized_members(self):
        for payload in ({"title": "   "}, {"participant_member_ids": [-1]}, {"participants": ["Free text"]}):
            self.assertEqual(self.create_meeting(**payload).status_code, 422)
        self.current_user_id = 3
        self.assertEqual(self.create_meeting().status_code, 403)


if __name__ == "__main__":
    unittest.main()
