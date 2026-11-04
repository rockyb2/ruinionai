import asyncio
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from hashlib import sha256
from pathlib import Path
from unittest.mock import AsyncMock, patch

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "email-tests-only-not-a-production-secret-key")
os.environ.setdefault("RATE_LIMIT_STORAGE_URI", "memory://")
os.environ["PUBLIC_REGISTRATION_ENABLED"] = "true"
os.environ["FRONTEND_URL"] = "https://app.example.test"
os.environ["RESEND_API_KEY"] = "re_test"
os.environ["RESEND_FROM_EMAIL"] = "bonjour@example.com"
os.environ["RESEND_REPLY_TO"] = "support@example.com"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth.rate_limit import limiter
from auth.routes import router as auth_router
from database import Base, get_db
from models import EmailVerificationToken, User
from services.email_service import send_email
from services.email_verification_service import verification_url


class EmailVerificationTests(unittest.TestCase):
    def setUp(self):
        os.environ["PUBLIC_REGISTRATION_ENABLED"] = "true"
        self.temp = tempfile.TemporaryDirectory()
        self.engine = create_engine(
            f"sqlite:///{Path(self.temp.name) / 'email-verification.db'}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)

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

    def register(self, ip="203.0.113.101"):
        sender = AsyncMock()
        with patch(
            "auth.routes.deliver_welcome_verification_email",
            new=sender,
        ):
            response = self.client.post(
                "/auth/register",
                headers={"X-Real-IP": ip},
                json={
                    "first_name": "Awa",
                    "last_name": "Kone",
                    "email": "awa@example.com",
                    "password": "MotDePasseSolide1!",
                    "organization_name": "Equipe Awa",
                    "terms_accepted": True,
                },
            )
        self.assertEqual(response.status_code, 201, response.text)
        self.assertNotIn("access_token", response.json())
        sender.assert_awaited_once()
        return sender.await_args.args[2]

    def test_registration_verification_and_login_flow(self):
        token = self.register()

        with self.sessions() as db:
            user = db.query(User).filter(User.email == "awa@example.com").one()
            self.assertIsNone(user.email_verified_at)
            verification = db.query(EmailVerificationToken).one()
            self.assertEqual(
                verification.token_hash,
                sha256(token.encode("utf-8")).hexdigest(),
            )
            self.assertNotEqual(verification.token_hash, token)

        blocked = self.client.post(
            "/auth/login",
            headers={"X-Real-IP": "203.0.113.102"},
            json={"email": "awa@example.com", "password": "MotDePasseSolide1!"},
        )
        self.assertEqual(blocked.status_code, 403, blocked.text)
        self.assertEqual(blocked.json()["detail"]["code"], "EMAIL_NOT_VERIFIED")

        verified = self.client.post(
            "/auth/verify-email",
            headers={"X-Real-IP": "203.0.113.103"},
            json={"token": token},
        )
        self.assertEqual(verified.status_code, 200, verified.text)
        self.assertTrue(verified.json()["verified"])

        repeated = self.client.post(
            "/auth/verify-email",
            headers={"X-Real-IP": "203.0.113.104"},
            json={"token": token},
        )
        self.assertEqual(repeated.status_code, 200, repeated.text)

        logged_in = self.client.post(
            "/auth/login",
            headers={"X-Real-IP": "203.0.113.105"},
            json={"email": "awa@example.com", "password": "MotDePasseSolide1!"},
        )
        self.assertEqual(logged_in.status_code, 200, logged_in.text)
        self.assertIn("access_token", logged_in.json())

    def test_expired_token_and_generic_resend_response(self):
        token = self.register(ip="203.0.113.111")
        with self.sessions() as db:
            verification = db.query(EmailVerificationToken).one()
            verification.expires_at = datetime.utcnow() - timedelta(minutes=1)
            verification.created_at = datetime.utcnow() - timedelta(minutes=5)
            db.commit()

        expired = self.client.post(
            "/auth/verify-email",
            headers={"X-Real-IP": "203.0.113.112"},
            json={"token": token},
        )
        self.assertEqual(expired.status_code, 410, expired.text)

        sender = AsyncMock()
        with patch(
            "auth.routes.deliver_welcome_verification_email",
            new=sender,
        ):
            existing = self.client.post(
                "/auth/resend-verification",
                headers={"X-Real-IP": "203.0.113.113"},
                json={"email": "awa@example.com"},
            )
            unknown = self.client.post(
                "/auth/resend-verification",
                headers={"X-Real-IP": "203.0.113.114"},
                json={"email": "absent@example.com"},
            )

        self.assertEqual(existing.status_code, 202, existing.text)
        self.assertEqual(unknown.status_code, 202, unknown.text)
        self.assertEqual(existing.json(), unknown.json())
        sender.assert_awaited_once()

    def test_email_service_builds_text_and_reply_to(self):
        send_async = AsyncMock(return_value={"id": "email_123"})
        with patch("services.email_service.resend.Emails.send_async", new=send_async):
            result = asyncio.run(
                send_email(
                    "user@example.com",
                    "Sujet",
                    "<p>Bonjour</p>",
                    text="Bonjour",
                )
            )

        self.assertEqual(result["id"], "email_123")
        params = send_async.await_args.args[0]
        self.assertEqual(params["from"], "RuinionAI <bonjour@example.com>")
        self.assertEqual(params["reply_to"], "support@example.com")
        self.assertEqual(params["text"], "Bonjour")

    def test_verification_url_keeps_token_out_of_http_query(self):
        url = verification_url("secret-token")
        self.assertEqual(
            url,
            "https://app.example.test/verifier-email#token=secret-token",
        )
        self.assertNotIn("?token=", url)


if __name__ == "__main__":
    unittest.main()
