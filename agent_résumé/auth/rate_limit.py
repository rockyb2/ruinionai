"""Limitation de débit des routes d'authentification publiques."""

import os

from slowapi import Limiter


def client_address(request) -> str:
    # Le backend n'est pas publié sur l'hôte. Nginx remplace X-Real-IP.
    forwarded = request.headers.get("x-real-ip", "").strip()
    if forwarded:
        return forwarded
    return request.client.host if request.client else "unknown"


limiter = Limiter(
    key_func=client_address,
    storage_uri=os.getenv("RATE_LIMIT_STORAGE_URI", "memory://"),
    headers_enabled=True,
)
