import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "security-tests-only-not-a-production-secret-key")
os.environ["PUBLIC_REGISTRATION_ENABLED"] = "false"
os.environ.setdefault("RATE_LIMIT_STORAGE_URI", "memory://")

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth.dependencies import get_current_user
from auth.rate_limit import limiter
from auth.routes import router as auth_router
from auth.security import create_access_token, hash_password, verify_password
from database import Base, get_db
from models import AuditLog, User


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.engine = create_engine(
            f"sqlite:///{Path(self.temp.name) / 'security.db'}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        with self.sessions() as db:
            db.add(
                User(
                    id=1,
                    first_name="Awa",
                    last_name="Kone",
                    email="awa@example.com",
                    password_hash=hash_password("MotDePasseSolide1!"),
                    is_active=True,
                    token_version=0,
                )
            )
            db.commit()

        app = FastAPI()
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        app.include_router(auth_router)

        @app.get("/protected")
        def protected(user: User = Depends(get_current_user)):
            return {"id": user.id}

        def test_db():
            with self.sessions() as db:
                yield db

        app.dependency_overrides[get_db] = test_db
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.engine.dispose()
        self.temp.cleanup()

    def test_password_hashing_and_bcrypt_byte_limit(self):
        password_hash = hash_password("MotDePasseSolide1!")
        self.assertTrue(verify_password("MotDePasseSolide1!", password_hash))
        self.assertFalse(verify_password("mauvais", password_hash))
        with self.assertRaisesRegex(ValueError, "72 octets"):
            hash_password("é" * 37)

    def test_logout_invalidates_existing_access_token(self):
        token = create_access_token("1", 0)
        headers = {"Authorization": f"Bearer {token}"}
        self.assertEqual(self.client.get("/protected", headers=headers).status_code, 200)
        self.assertEqual(self.client.post("/auth/logout", headers=headers).status_code, 204)
        self.assertEqual(self.client.get("/protected", headers=headers).status_code, 401)

    def test_public_registration_is_disabled_by_default(self):
        response = self.client.post(
            "/auth/register",
            headers={"X-Real-IP": "198.51.100.10"},
            json={
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "password": "MotDePasseSolide1!",
                "organization_name": "Test organisation",
            },
        )
        self.assertEqual(response.status_code, 403, response.text)

    def test_login_is_rate_limited_by_network_identifier(self):
        statuses = []
        for _ in range(6):
            response = self.client.post(
                "/auth/login",
                headers={"X-Real-IP": "198.51.100.20"},
                json={"email": "absent@example.com", "password": "mauvais"},
            )
            statuses.append(response.status_code)
        self.assertEqual(statuses[:5], [401] * 5)
        self.assertEqual(statuses[5], 429)

    def test_account_lockout_and_audit_log(self):
        with self.sessions() as db:
            user = db.get(User, 1)
            user.failed_login_attempts = 9
            db.commit()

        response = self.client.post(
            "/auth/login",
            headers={"X-Real-IP": "198.51.100.30"},
            json={"email": "awa@example.com", "password": "mauvais"},
        )
        self.assertEqual(response.status_code, 401)

        blocked = self.client.post(
            "/auth/login",
            headers={"X-Real-IP": "198.51.100.31"},
            json={"email": "awa@example.com", "password": "MotDePasseSolide1!"},
        )
        self.assertEqual(blocked.status_code, 429)
        with self.sessions() as db:
            user = db.get(User, 1)
            self.assertIsNotNone(user.locked_until)
            actions = [entry.action for entry in db.query(AuditLog).all()]
            self.assertIn("AUTH_LOGIN_FAILED", actions)
            self.assertIn("AUTH_LOGIN_BLOCKED", actions)


if __name__ == "__main__":
    unittest.main()
