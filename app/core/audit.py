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
    """Insert a row into audit_logs for a session-related action."""
    db.execute(
        text("""
            INSERT INTO audit_logs
                (actor_id, actor_role, action, entity_type, entity_id, organization_id, ip_address)
            VALUES
                (:actor_id, :actor_role, :action, 'session', :entity_id, :organization_id, :ip_address)
        """),
        {
            "actor_id":        actor_id,
            "actor_role":      actor_role,
            "action":          action,
            "entity_id":       session_id,
            "organization_id": org_id,
            "ip_address":      ip_address,
        },
    )
