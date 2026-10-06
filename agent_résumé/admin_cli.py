"""Commandes locales sensibles de l'administration de la plateforme."""
import argparse

from sqlalchemy import func

from database import SessionLocal
from models import User


def change_platform_admin(db, email: str, enabled: bool) -> User:
    normalized = email.strip().lower()
    user = (
        db.query(User)
        .filter(func.lower(User.email) == normalized)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if user is None:
        raise ValueError("Aucun compte ne correspond à cet e-mail.")
    if not user.is_active:
        raise ValueError("Le compte doit être actif.")
    if not enabled and user.is_super_admin:
        count = db.query(User).filter(User.is_super_admin.is_(True)).count()
        if count <= 1:
            raise ValueError("Impossible de retirer le dernier super administrateur.")
    user.is_super_admin = enabled
    db.commit()
    db.refresh(user)
    return user


def main():
    parser = argparse.ArgumentParser(description="Accorder ou retirer l'accès super administrateur.")
    parser.add_argument("action", choices=("grant", "revoke"))
    parser.add_argument("email")
    args = parser.parse_args()
    with SessionLocal() as db:
        try:
            user = change_platform_admin(db, args.email, args.action == "grant")
        except ValueError as error:
            db.rollback()
            parser.error(str(error))
    state = "accordé" if user.is_super_admin else "retiré"
    print(f"Accès super administrateur {state} pour {user.email}.")


if __name__ == "__main__":
    main()
