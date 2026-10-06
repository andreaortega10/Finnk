import json
from sqlalchemy.orm import Session
from ..models import AuditLog

def log_audit(
    db: Session,
    user_id: int,
    entity_type: str,
    entity_id: int,
    action: str,
    details: dict = None
):
    try:
        details_str = json.dumps(details, default=str) if details else None
        audit_entry = AuditLog(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            details_json=details_str
        )
        db.add(audit_entry)
        db.commit()
    except Exception as e:
        print(f"Erro ao salvar log de auditoria: {e}")
