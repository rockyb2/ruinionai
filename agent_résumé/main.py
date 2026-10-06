import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth.routes import router as auth_router
from routes.meetings import router as meetings_router
from routes.organization import router as organization_router
from routes.invitations import router as invitations_router
from routes.notifications import router as notifications_router
from routes.admin.router import router as admin_router
from routes.invitation_acceptance import (
    router as invitation_acceptance_router,
)


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


app = FastAPI(title="RuinionAI Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
