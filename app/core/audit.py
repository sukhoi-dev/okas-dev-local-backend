from sqlalchemy.orm import Session
from sqlalchemy import text


def write_session_audit(
    db: Session,
    actor_id,
    actor_role,
    action: str,
    session_id,
    ip_address,
    org_id=None,
) -> None:
    db.execute(
        text("""
            INSERT INTO audit_logs
                (user_id, action, entity_type, entity_id, organization_id, ip_address)
            VALUES
                (:user_id, :action, 'session', :entity_id, :organization_id, :ip_address)
        """),
        {
            "user_id":         actor_id,
            "action":          action,
            "entity_id":       session_id,
            "organization_id": org_id,
            "ip_address":      ip_address,
        },
    )
