from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError


def get_record(db, model, record_id, lock=False):
    query = db.query(model).filter(model.id == record_id)
    if lock:
        query = query.populate_existing().with_for_update()
    record = query.first()
    if record is None:
        raise HTTPException(404, "Cet élément est introuvable.")
    return record


def commit(db):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Ce nom ou cet e-mail existe déjà, ou cet élément est encore utilisé.") from exc


def page(query, offset, limit, serialize):
    return {"total": query.count(), "offset": offset, "limit": limit,
            "items": [serialize(item) for item in query.offset(offset).limit(limit).all()]}
