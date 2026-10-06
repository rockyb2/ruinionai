from fastapi import APIRouter, Depends

from auth.dependencies import require_platform_admin
from models import User
from routes.admin.organisation_admin import router as organizations
from routes.admin.users import router as users
from routes.admin.meetings import router as meetings
from schema import UserRead

router = APIRouter(prefix="/admin", tags=["Administration"], dependencies=[Depends(require_platform_admin)])


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(require_platform_admin)):
    # Indépendant du contexte d'organisation : un administrateur peut n'avoir
    # aucune équipe ou appartenir à plusieurs organisations.
    return user


router.include_router(organizations)
router.include_router(users)
router.include_router(meetings)
