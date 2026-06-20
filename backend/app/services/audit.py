import json

from sqlalchemy.orm import Session

from app.db.models import AuditLog


def register_audit_log(
    db: Session,
    *,
    actor_id: int | None,
    entity: str,
    entity_id: int,
    action: str,
    payload: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_id=actor_id,
            entity=entity,
            entity_id=entity_id,
            action=action,
            payload=json.dumps(payload, ensure_ascii=False) if payload else None,
        )
    )
