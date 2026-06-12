from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.base import get_session
from app.core.security import hash_value

_bearer = HTTPBearer()


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_session),
) -> dict:
    """
    FastAPI dependency that validates a Bearer session token and returns the
    current user context dict.
    """
    raw_token = credentials.credentials
    token_hash = hash_value(raw_token)

    session_row = db.execute(
        text("""
            SELECT id, user_id, ip_address, expires_at
            FROM app_sessions
            WHERE token_hash = :token_hash
            LIMIT 1
        """),
        {"token_hash": token_hash},
    ).mappings().fetchone()

    if not session_row:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")

    # Check expiry inside the DB to avoid timezone skew
    still_valid = db.execute(
        text("SELECT expires_at > UTC_TIMESTAMP() AS valid FROM app_sessions WHERE id = :id"),
        {"id": session_row["id"]},
    ).mappings().fetchone()

    if not still_valid or not still_valid["valid"]:
        raise HTTPException(status_code=401, detail="Session has expired")

    # Touch last_active_at
    db.execute(
        text("UPDATE app_sessions SET last_active_at = NOW(3) WHERE id = :id"),
        {"id": session_row["id"]},
    )

    # Fetch the user
    user_row = db.execute(
        text("""
            SELECT id, full_name, email, phone, organization_id, active_ind
            FROM app_users
            WHERE id = :user_id
            LIMIT 1
        """),
        {"user_id": session_row["user_id"]},
    ).mappings().fetchone()

    if not user_row:
        raise HTTPException(status_code=401, detail="User not found")

    if not user_row["active_ind"]:
        raise HTTPException(status_code=403, detail="Account is inactive")

    # Fetch the user's role
    role_row = db.execute(
        text("""
            SELECT r.name
            FROM app_user_roles aur
            JOIN roles r ON r.id = aur.role_id
            WHERE aur.user_id = :user_id
            LIMIT 1
        """),
        {"user_id": user_row["id"]},
    ).mappings().fetchone()

    role = role_row["name"] if role_row else None

    ip_address = request.client.host if request.client else session_row["ip_address"]

    return {
        "session_id": session_row["id"],
        "user": {
            "id":              user_row["id"],
            "full_name":       user_row["full_name"],
            "email":           user_row["email"],
            "phone":           user_row["phone"],
            "organization_id": user_row["organization_id"],
            "role":            role,
        },
        "token_hash": token_hash,
        "ip_address":  ip_address,
    }
