import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "admin-tests-only-not-a-production-secret-key")

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from auth.dependencies import get_current_user
from database import Base, get_db
from models import Meeting, Organization, OrganizationMember, User
from routes.admin.router import router
from admin_cli import change_platform_admin


class AdminRoutesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.engine = create_engine(
            f"sqlite:///{Path(self.temp.name) / 'admin.db'}",
            connect_args={"check_same_thread": False},
        )
        event.listen(
            self.engine,
            "connect",
            lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"),
        )
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        with self.sessions() as db:
            db.add_all(
                [
                    User(
                        id=1,
                        first_name="Super",
                        last_name="Admin",
                        email="admin@example.com",
                        password_hash="x",
                        is_active=True,
                        is_super_admin=True,
                    ),
                    User(
                        id=2,
                        first_name="Awa",
                        last_name="Koné",
                        email="awa@example.com",
                        password_hash="x",
                        is_active=True,
                    ),
                    User(
                        id=3,
                        first_name="Noël",
                        last_name="Kouamé",
                        email="noel@example.com",
                        password_hash="x",
                        is_active=True,
                    ),
                ]
            )
            db.add(Organization(id=1, name="Ivoir Trips", description="Tourisme"))
            db.flush()
            db.add_all(
                [
                    OrganizationMember(
                        id=1,
                        organization_id=1,
                        user_id=2,
                        role="owner",
                        status="active",
                    ),
                    OrganizationMember(
                        id=2,
                        organization_id=1,
                        user_id=3,
                        role="member",
                        status="active",
                    ),
                ]
            )
            db.add(
                Meeting(
                    id=1,
                    organization_id=1,
                    title="Réunion",
                    created_by_user_id=2,
                    audio_duration=3600,
                    processing_status="completed",
                )
            )
            db.commit()
        self.current_user_id = 1
        app = FastAPI()
        app.include_router(router)

        def test_db():
            with self.sessions() as db:
                yield db

        def current_user(db=Depends(get_db)):
            return db.get(User, self.current_user_id)

        app.dependency_overrides[get_db] = test_db
        app.dependency_overrides[get_current_user] = current_user
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.engine.dispose()
        self.temp.cleanup()

    def test_routes_require_super_admin_and_counts_are_not_multiplied(self):
        response = self.client.get("/admin/organizations")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["items"][0]["members_count"], 2)
        self.assertEqual(response.json()["items"][0]["meetings_count"], 1)
        self.current_user_id = 2
        self.assertEqual(self.client.get("/admin/organizations").status_code, 403)

    def test_organization_crud_preserves_last_owner(self):
        created = self.client.post(
            "/admin/organizations",
            json={
                "name": "Nouvelle équipe",
                "description": "Test",
                "owner_user_id": 3,
            },
        )
        self.assertEqual(created.status_code, 201, created.text)
        org_id = created.json()["id"]
        forbidden = self.client.delete(f"/admin/organizations/{org_id}/members/3")
        self.assertEqual(forbidden.status_code, 409, forbidden.text)
        self.assertEqual(
            self.client.delete(f"/admin/organizations/{org_id}").status_code, 204
        )

    def test_user_and_meeting_crud_guards(self):
        self.assertEqual(self.client.delete("/admin/users/1").status_code, 409)
        self.assertEqual(
            self.client.patch("/admin/users/2", json={"is_active": False}).status_code,
            409,
        )
        meeting = self.client.post(
            "/admin/meetings",
            json={
                "organization_id": 1,
                "title": "Créée par admin",
            },
        )
        self.assertEqual(meeting.status_code, 201, meeting.text)
        meeting_id = meeting.json()["id"]
        
        private_fields = {
            "transcription",
            "transcription_segments",
            "summary",
            "summary_short",
            "summary_long",
            "participants",
            "audio_path",
            "audio_manifest",
            "report_path",
        }

        created_data = meeting.json()

        self.assertTrue(
            private_fields.isdisjoint(created_data),
            created_data,
        )

        detail_response = self.client.get(
            f"/admin/meetings/{meeting_id}"
        )

        self.assertEqual(
            detail_response.status_code,
            200,
            detail_response.text,
        )

        self.assertTrue(
            private_fields.isdisjoint(detail_response.json()),
            detail_response.json(),
        )

        self.assertEqual(
            self.client.get(
                f"/admin/meetings/{meeting_id}/audio"
            ).status_code,
            403,
        )

        self.assertEqual(
            self.client.get(
                f"/admin/meetings/{meeting_id}/report"
            ).status_code,
            403,
        )
        
        
        
        
        
        self.assertEqual(
            self.client.patch(
                f"/admin/meetings/{meeting_id}", json={"title": "Titre corrigé"}
            ).status_code,
            200,
        )
        with self.sessions() as db:
            row = db.get(Meeting, meeting_id)
            row.processing_status = "writing"
            db.commit()
        self.assertEqual(
            self.client.delete(f"/admin/meetings/{meeting_id}").status_code, 409
        )

    def test_cli_can_bootstrap_but_not_remove_last_super_admin(self):
        with self.sessions() as db:
            promoted = change_platform_admin(db, "awa@example.com", True)
            self.assertTrue(promoted.is_super_admin)
            change_platform_admin(db, "awa@example.com", False)
            with self.assertRaisesRegex(ValueError, "dernier super administrateur"):
                change_platform_admin(db, "admin@example.com", False)


if __name__ == "__main__":
    unittest.main()
