import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "password-reset-tests-only-secret-key-123456")
os.environ.setdefault("RATE_LIMIT_STORAGE_URI", "memory://")
os.environ["RESEND_API_KEY"] = "re_test"
os.environ["RESEND_FROM_EMAIL"] = "bonjour@example.com"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth.rate_limit import limiter
from auth.routes import router as auth_router
from auth.security import hash_password
from database import Base, get_db
from models import PasswordResetCode, User
from services.password_reset_service import hash_reset_code


class PasswordResetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.engine = create_engine(
            f"sqlite:///{Path(self.temp.name) / 'password-reset.db'}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)

        with self.sessions() as db:
            db.add(
                User(
                    first_name="Awa",
                    last_name="Kone",
                    email="awa@example.com",
                    password_hash=hash_password("AncienMotDePasse1!"),
                    is_active=True,
                    email_verified_at=datetime.utcnow(),
                )
            )
            db.commit()

        app = FastAPI()
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        app.include_router(auth_router)

        def test_db():
            with self.sessions() as db:
                yield db

        app.dependency_overrides[get_db] = test_db
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.engine.dispose()
        self.temp.cleanup()

    def request_code(self, ip="203.0.113.201"):
        sender = AsyncMock()
        with patch(
            "auth.routes.deliver_password_reset_code_email",
            new=sender,
        ):
            response = self.client.post(
                "/auth/forgot-password",
                headers={"X-Real-IP": ip},
                json={"email": "awa@example.com"},
            )
        self.assertEqual(response.status_code, 202, response.text)
        sender.assert_awaited_once()
        return response, sender.await_args.args[2]

    def test_request_is_generic_and_code_is_not_stored_in_plaintext(self):
        response, code = self.request_code()
        unknown = self.client.post(
            "/auth/forgot-password",
            headers={"X-Real-IP": "203.0.113.202"},
            json={"email": "absent@example.com"},
        )

        self.assertEqual(unknown.status_code, 202, unknown.text)
        self.assertEqual(response.json(), unknown.json())
        self.assertRegex(code, r"^\d{8}$")

        with self.sessions() as db:
            user = db.query(User).filter(User.email == "awa@example.com").one()
            reset_code = db.query(PasswordResetCode).one()
            self.assertNotEqual(reset_code.code_hash, code)
            self.assertEqual(reset_code.code_hash, hash_reset_code(user.id, code))

    def test_valid_code_changes_password_and_invalidates_sessions(self):
        _, code = self.request_code(ip="203.0.113.211")

        invalid = self.client.post(
            "/auth/verify-password-reset-code",
            headers={"X-Real-IP": "203.0.113.212"},
            json={
                "email": "awa@example.com",
                "code": "00000000" if code != "00000000" else "99999999",
            },
        )
        self.assertEqual(invalid.status_code, 400, invalid.text)

        verified = self.client.post(
            "/auth/verify-password-reset-code",
            headers={"X-Real-IP": "203.0.113.213"},
            json={"email": "awa@example.com", "code": code},
        )
        self.assertEqual(verified.status_code, 200, verified.text)
        reset_token = verified.json()["reset_token"]

        confirmation = AsyncMock()
        with patch(
            "auth.routes.deliver_password_changed_email",
            new=confirmation,
        ):
            changed = self.client.post(
                "/auth/reset-password",
                headers={"X-Real-IP": "203.0.113.214"},
                json={
                    "reset_token": reset_token,
                    "new_password": "NouveauMotDePasse2!",
                },
            )

        self.assertEqual(changed.status_code, 200, changed.text)
        confirmation.assert_awaited_once()

        old_login = self.client.post(
            "/auth/login",
            headers={"X-Real-IP": "203.0.113.215"},
            json={"email": "awa@example.com", "password": "AncienMotDePasse1!"},
        )
        new_login = self.client.post(
            "/auth/login",
            headers={"X-Real-IP": "203.0.113.216"},
            json={"email": "awa@example.com", "password": "NouveauMotDePasse2!"},
        )
        self.assertEqual(old_login.status_code, 401, old_login.text)
        self.assertEqual(new_login.status_code, 200, new_login.text)

        with self.sessions() as db:
            user = db.query(User).filter(User.email == "awa@example.com").one()
            reset_code = db.query(PasswordResetCode).one()
            self.assertEqual(user.token_version, 1)
            self.assertIsNotNone(reset_code.used_at)

        reused = self.client.post(
            "/auth/reset-password",
            headers={"X-Real-IP": "203.0.113.217"},
            json={
                "reset_token": reset_token,
                "new_password": "EncoreUnMotDePasse3!",
            },
        )
        self.assertEqual(reused.status_code, 400, reused.text)


if __name__ == "__main__":
    unittest.main()
