import asyncio
import os
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from auth.routes import router as auth_router
from auth.rate_limit import limiter
from routes.meetings import router as meetings_router
from routes.organization import router as organization_router
from routes.invitations import router as invitations_router
from routes.notifications import router as notifications_router
from routes.admin.router import router as admin_router
from routes.invitation_acceptance import (
    router as invitation_acceptance_router,
)
from security_middleware import AuditMiddleware, SecurityHeadersMiddleware, is_production


@asynccontextmanager
async def lifespan(app):
    from meeting_processing import worker_loop
    worker = asyncio.create_task(worker_loop())
    try:
        yield
    finally:
        worker.cancel()
        with suppress(asyncio.CancelledError):
            await worker


production = is_production()
app = FastAPI(
    title="RuinionAI Backend",
    lifespan=lifespan,
    docs_url=None if production else "/docs",
    redoc_url=None if production else "/redoc",
    openapi_url=None if production else "/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def cors_origins() -> list[str]:
    configured = os.getenv("CORS_ORIGINS", "").strip()
    if configured:
        origins = [value.strip() for value in configured.split(",") if value.strip()]
        if "*" in origins:
            raise RuntimeError("CORS_ORIGINS ne peut pas contenir '*' avec des identifiants.")
        return origins
    if production:
        return []
    return [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Organization-Id"],
)

app.add_middleware(AuditMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}

app.include_router(auth_router)
app.include_router(meetings_router)
app.include_router(organization_router)
app.include_router(invitations_router)
app.include_router(notifications_router)
app.include_router(invitation_acceptance_router)
app.include_router(admin_router)
