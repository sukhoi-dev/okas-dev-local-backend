from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.base import get_session
from app.core.session import get_current_user
from app.core.audit import write_session_audit
from app.auth import get_current_user as jwt_get_current_user
from app.db import get_db

router = APIRouter(prefix="/api/auth", tags=["auth | session"], redirect_slashes=False)


# ── GET /auth/me ──────────────────────────────────────────────────────────────

@router.get("/me")
def me(current: dict = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return {"success": True, "user": current["user"]}


# ── GET /auth/permissions ─────────────────────────────────────────────────────

@router.get("/permissions")
def get_permissions(current_user: dict = Depends(jwt_get_current_user)):
    """Return the current user's permissions as a flat list and grouped dict."""
    user_id = current_user["user_id"]
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT rp.feature_key, rp.action_key, rp.is_allowed
                FROM app_user_roles aur
                JOIN role_permissions rp ON rp.role_id = aur.role_id
                WHERE aur.user_id = %s
                """,
                (user_id,),
            )
            rows = cur.fetchall()

    flat = []
    grouped = {}
    for row in rows:
        feature   = row["feature_key"]
        action    = row["action_key"]
        is_allowed = bool(row["is_allowed"])
        grouped.setdefault(feature, {})[action] = is_allowed
        if is_allowed:
            flat.append(f"{feature}.{action}")

    return {"success": True, "permissions": {"flat": flat, "grouped": grouped}}


# ── POST /auth/logout ─────────────────────────────────────────────────────────

@router.post("/logout")
def logout(
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Delete the current session and record an audit entry."""
    session_id = current["session_id"]
    user       = current["user"]

    db.execute(
        text("DELETE FROM app_sessions WHERE id = :id"),
        {"id": session_id},
    )

    write_session_audit(
        db=db,
        user_id=user["id"],
        action="session.logout",
        session_id=session_id,
        ip_address=current["ip_address"],
        org_id=user["organization_id"],
    )

    return {"success": True, "message": "Logged out"}
