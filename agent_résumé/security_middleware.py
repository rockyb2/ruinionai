"""En-têtes HTTP et journalisation transversale des mutations authentifiées."""

import logging
import os

from starlette.middleware.base import BaseHTTPMiddleware

from audit_service import add_audit_log
from database import SessionLocal


logger = logging.getLogger(__name__)
STATE_CHANGING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def is_production() -> bool:
    return os.getenv("ENVIRONMENT", "development").strip().lower() == "production"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), geolocation=(), payment=(), usb=()"
        )
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        if is_production():
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
            )
            if request.headers.get("x-forwarded-proto") == "https":
                response.headers["Strict-Transport-Security"] = (
                    "max-age=31536000; includeSubDomains"
                )
        return response


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        actor_id = getattr(request.state, "current_user_id", None)
        if (
            actor_id
            and request.method in STATE_CHANGING_METHODS
            and not request.url.path.startswith("/auth/")
        ):
            parts = [part for part in request.url.path.split("/") if part]
            target_type = parts[1] if parts and parts[0] == "admin" and len(parts) > 1 else (parts[0] if parts else None)
            target_id = next((part for part in reversed(parts) if part.isdigit()), None)
            db = SessionLocal()
            try:
                add_audit_log(
                    db,
                    action=f"HTTP_{request.method}",
                    request=request,
                    actor_id=actor_id,
                    target_type=target_type,
                    target_id=target_id,
                    status_code=response.status_code,
                )
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("Impossible d'enregistrer le journal d'audit")
            finally:
                db.close()
        return response
