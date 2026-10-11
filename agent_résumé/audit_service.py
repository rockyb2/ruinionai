"""Journaux d'audit sans contenu privé ni adresse IP en clair."""

import hashlib
import hmac
from typing import Any

from auth.security import SECRET_KEY
from models import AuditLog


def request_ip(request) -> str:
    value = request.headers.get("x-real-ip", "").strip()
    if value:
        return value
    return request.client.host if request.client else "unknown"


def hash_ip(value: str) -> str:
    return hmac.new(
        SECRET_KEY.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def add_audit_log(
    db,
    *,
    action: str,
    request=None,
    actor_id: int | None = None,
    target_type: str | None = None,
    target_id: str | int | None = None,
    status_code: int | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_id=actor_id,
        action=action[:80],
        target_type=target_type[:80] if target_type else None,
        target_id=str(target_id)[:120] if target_id is not None else None,
        method=request.method[:10] if request else None,
        path=str(request.url.path)[:500] if request else None,
        status_code=status_code,
        ip_hash=hash_ip(request_ip(request)) if request else None,
        details=details or None,
    )
    db.add(entry)
    return entry
