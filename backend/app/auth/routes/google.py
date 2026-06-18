import requests as http
from datetime import datetime, timedelta
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.base import get_session
from app.core.security import generate_session_token, hash_value
from app.core.audit import write_session_audit

router = APIRouter(prefix="/auth/google", tags=["auth | google"], redirect_slashes=False)

_SESSION_EXPIRY_DAYS = 30
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


# ── Pydantic schema ───────────────────────────────────────────────────────────

class GoogleLoginRequest(BaseModel):
    access_token: str
    keep_logged_in: bool = False


# ── Internal helpers ──────────────────────────────────────────────────────────

def _verify_google_token(access_token: str) -> dict:
    resp = http.get(
        _GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google access token")
    data = resp.json()
    if not data.get("sub"):
        raise HTTPException(status_code=401, detail="Google token missing subject")
    return {
        "sub":     data["sub"],
        "email":   data.get("email", "").lower().strip(),
        "name":    data.get("name"),
        "picture": data.get("picture"),
    }


def _get_user_type_and_role(db: Session, user_id: int, email: str) -> Tuple[str, Optional[str]]:
    org = db.execute(
        text("SELECT id FROM organizations WHERE email = :email AND active_ind = 1 LIMIT 1"),
        {"email": email},
    ).mappings().fetchone()
    user_type = "si_distributor" if org else "member"

    role_row = db.execute(
        text("""
            SELECT r.name
            FROM app_user_roles aur
            JOIN roles r ON r.id = aur.role_id
            WHERE aur.user_id = :user_id
            LIMIT 1
        """),
        {"user_id": user_id},
    ).mappings().fetchone()

    return user_type, (role_row["name"] if role_row else None)


def _create_session(
    db: Session,
    user_id: int,
    ip_address: Optional[str],
    keep_logged_in: bool = False,
) -> Tuple[str, datetime]:
    raw_token  = generate_session_token()
    token_hash = hash_value(raw_token)
    expires_at = (
        datetime.utcnow() + timedelta(days=_SESSION_EXPIRY_DAYS)
        if keep_logged_in
        else datetime.utcnow() + timedelta(hours=2)
    )

    db.execute(
        text("""
            INSERT INTO app_sessions (user_id, token_hash, ip_address, expires_at, last_active_at)
            VALUES (:user_id, :token_hash, :ip, :expires_at, NOW(3))
        """),
        {
            "user_id":    user_id,
            "token_hash": token_hash,
            "ip":         ip_address,
            "expires_at": expires_at,
        },
    )

    session_row = db.execute(
        text("SELECT id FROM app_sessions WHERE token_hash = :token_hash LIMIT 1"),
        {"token_hash": token_hash},
    ).mappings().fetchone()

    return raw_token, expires_at, (session_row["id"] if session_row else None)


def _build_response(raw_token, expires_at, user_type, role, user) -> dict:
    return {
        "success":    True,
        "token":      raw_token,
        "expires_at": expires_at.isoformat(),
        "user_type":  user_type,
        "user": {
            "id":              user["id"],
            "full_name":       user["full_name"],
            "email":           user["email"],
            "phone":           user["phone"],
            "organization_id": user["organization_id"],
            "role":            role,
        },
    }


# ── POST /auth/google/login ───────────────────────────────────────────────────

@router.post("/login")
def google_login(body: GoogleLoginRequest, request: Request, db: Session = Depends(get_session)):
    """
    Google OAuth login for app_users.

    Accepts a Google access_token from the frontend (obtained via useGoogleLogin).
    Verifies it against Google's userinfo endpoint to extract sub + email.

    Case 1 — google_id found         : log in directly.
    Case 2 — email found, no google_id: link google_id to existing account, log in.
    Case 3 — email not found         : 401 — user must be registered by an admin first.
    """
    payload    = _verify_google_token(body.access_token)
    google_sub = payload["sub"]
    email      = payload["email"]
    avatar_url = payload["picture"]

    ip_address = request.client.host if request.client else None

    # ── Case 1: known google_id ───────────────────────────────────────────────
    user = db.execute(
        text("""
            SELECT id, full_name, email, phone, organization_id, active_ind
            FROM app_users
            WHERE google_id = :google_id
            LIMIT 1
        """),
        {"google_id": google_sub},
    ).mappings().fetchone()

    if user:
        if not user["active_ind"]:
            raise HTTPException(status_code=403, detail="Account is inactive")

        db.execute(
            text("UPDATE app_users SET last_login_at = NOW(3) WHERE id = :id"),
            {"id": user["id"]},
        )
        user_type, role = _get_user_type_and_role(db, user["id"], user["email"])
        raw_token, expires_at, session_id = _create_session(
            db, user["id"], ip_address, keep_logged_in=body.keep_logged_in
        )
        write_session_audit(
            db=db,
            actor_id=user["id"],
            actor_role=role,
            action="session.login",
            session_id=session_id,
            ip_address=ip_address,
            org_id=user["organization_id"],
        )
        return _build_response(raw_token, expires_at, user_type, role, dict(user))

    # ── Case 2: email found, google_id not yet linked ─────────────────────────
    user = db.execute(
        text("""
            SELECT id, full_name, email, phone, organization_id, active_ind
            FROM app_users
            WHERE email = :email
            LIMIT 1
        """),
        {"email": email},
    ).mappings().fetchone()

    if user:
        if not user["active_ind"]:
            raise HTTPException(status_code=403, detail="Account is inactive")

        db.execute(
            text("""
                UPDATE app_users
                SET google_id     = :google_id,
                    avatar_url    = COALESCE(avatar_url, :avatar_url),
                    last_login_at = NOW(3)
                WHERE id = :id
            """),
            {"google_id": google_sub, "avatar_url": avatar_url, "id": user["id"]},
        )
        user_type, role = _get_user_type_and_role(db, user["id"], user["email"])
        raw_token, expires_at, session_id = _create_session(
            db, user["id"], ip_address, keep_logged_in=body.keep_logged_in
        )
        write_session_audit(
            db=db,
            actor_id=user["id"],
            actor_role=role,
            action="session.login",
            session_id=session_id,
            ip_address=ip_address,
            org_id=user["organization_id"],
        )
        return _build_response(raw_token, expires_at, user_type, role, dict(user))

    # ── Case 3: user does not exist ───────────────────────────────────────────
    raise HTTPException(
        status_code=401,
        detail="User not registered. Please contact your admin.",
    )
