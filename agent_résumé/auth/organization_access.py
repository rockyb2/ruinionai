from fastapi import HTTPException
from sqlalchemy.orm import Session

from auth.dependencies import AuthContext
from models import Organization, OrganizationMember


def lock_organization(db: Session, auth: AuthContext) -> OrganizationMember:
    # Meme verrou pour les invitations et la gestion des membres.
    organization_id = auth.membership.organization_id
    organization = (
        db.query(Organization)
        .filter(Organization.id == organization_id)
        .with_for_update()
        .first()
    )
    if organization is None:
        raise HTTPException(404, "Organisation introuvable.")

    # Relire les droits apres l'attente eventuelle du verrou.
    actor = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == auth.user.id,
        )
        .populate_existing()
        .first()
    )
    if actor is None or actor.status != "active" or actor.role not in ("owner", "admin"):
        raise HTTPException(403, "Droits administrateur requis.")

    return actor
