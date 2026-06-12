from fastapi import Depends, Header, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.base import get_session


def require_distributor(
    distributor_id: int = Path(...),
    authorization: str = Header(...),
    db: Session = Depends(get_session),
) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token_hash = authorization[7:]

    row = db.execute(
        text("""
            SELECT u.id AS user_id, u.organization_id
            FROM app_sessions s
            JOIN app_users u ON u.id = s.user_id
            WHERE s.token_hash = :hash
              AND s.expires_at > NOW(3)
              AND u.active_ind = 1
        """),
        {"hash": token_hash},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    role = db.execute(
        text("""
            SELECT 1 FROM app_user_roles aur
            JOIN roles r ON r.id = aur.role_id
            WHERE aur.user_id = :uid AND r.name = 'distributor'
            LIMIT 1
        """),
        {"uid": row.user_id},
    ).fetchone()

    if not role:
        raise HTTPException(status_code=403, detail="Distributor role required")

    if row.organization_id != distributor_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return {"user_id": row.user_id, "organization_id": row.organization_id}
