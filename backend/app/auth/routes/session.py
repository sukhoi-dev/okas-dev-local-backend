from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.base import get_session
from app.core.session import get_current_user
from app.core.audit import write_session_audit

router = APIRouter(prefix="/auth", tags=["auth | session"], redirect_slashes=False)


# ── GET /auth/me ──────────────────────────────────────────────────────────────

@router.get("/me")
def me(current: dict = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return {"success": True, "user": current["user"]}


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
        actor_id=user["id"],
        actor_role=user["role"],
        action="session.logout",
        session_id=session_id,
        ip_address=current["ip_address"],
        org_id=user["organization_id"],
    )

    return {"success": True, "message": "Logged out"}
