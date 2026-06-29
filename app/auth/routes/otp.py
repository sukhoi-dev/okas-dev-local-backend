from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.base import get_session
from app.core.security import generate_otp, hash_value, generate_session_token
from app.core.email import send_otp_email
from app.core.audit import write_session_audit
from app.auth import create_access_token

router = APIRouter(prefix="/api/auth/otp", tags=["auth | otp"], redirect_slashes=False)

_OTP_EXPIRY_MINUTES = 10
_SESSION_EXPIRY_DAYS = 30


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class OtpSendRequest(BaseModel):
    email: EmailStr


class OtpVerifyRequest(BaseModel):
    email: EmailStr
    otp: str
    keep_logged_in: bool = False


# ── Internal helper ───────────────────────────────────────────────────────────

def _resolve_user(db: Session, email: str) -> tuple:
    row = db.execute(
        text("""
            SELECT u.id, u.full_name, u.email, u.phone, u.organization_id, u.active_ind,
                   o.org_type
            FROM app_users u
            JOIN organizations o ON o.id = u.organization_id
            WHERE u.email = :email
            LIMIT 1
        """),
        {"email": email},
    ).mappings().fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Email not registered")

    if not row["active_ind"]:
        raise HTTPException(status_code=403, detail="Account is inactive")

    user     = dict(row)
    org_type = row["org_type"]

    org_email_row = db.execute(
        text("SELECT 1 FROM organizations WHERE email = :email LIMIT 1"),
        {"email": email},
    ).fetchone()
    if not org_email_row:
        org_type = "member"

    user_type = "si_distributor" if org_type in ("distributor", "si") else "member"

    role_row = db.execute(
        text("""
            SELECT r.name
            FROM app_user_roles aur
            JOIN roles r ON r.id = aur.role_id
            WHERE aur.user_id = :user_id
            LIMIT 1
        """),
        {"user_id": user["id"]},
    ).mappings().fetchone()

    user["role"]     = role_row["name"] if role_row else None
    user["org_type"] = org_type
    return user, user_type


# ── POST /api/auth/otp/send ───────────────────────────────────────────────────

@router.post("/send")
def send_otp(body: OtpSendRequest, db: Session = Depends(get_session)):
    _, user_type = _resolve_user(db, body.email)

    db.execute(
        text("""
            UPDATE app_otp_codes
            SET used_at = UTC_TIMESTAMP(3)
            WHERE email = :email
              AND purpose = 'login'
              AND used_at IS NULL
              AND expires_at > UTC_TIMESTAMP(3)
        """),
        {"email": body.email},
    )

    otp        = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=_OTP_EXPIRY_MINUTES)

    db.execute(
        text("""
            INSERT INTO app_otp_codes (email, code_hash, purpose, expires_at)
            VALUES (:email, :code_hash, 'login', :expires_at)
        """),
        {"email": body.email, "code_hash": hash_value(otp), "expires_at": expires_at},
    )

    try:
        send_otp_email(body.email, otp)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to send OTP email: {exc}")

    return {
        "success":   True,
        "message":   "OTP sent to email",
        "user_type": user_type,
    }


# ── POST /api/auth/otp/verify ─────────────────────────────────────────────────

@router.post("/verify")
def verify_otp(body: OtpVerifyRequest, request: Request, db: Session = Depends(get_session)):
    user, user_type = _resolve_user(db, body.email)

    otp_record = db.execute(
        text("""
            SELECT id, code_hash, expires_at, used_at
            FROM app_otp_codes
            WHERE email = :email AND purpose = 'login'
            ORDER BY created_at DESC
            LIMIT 1
        """),
        {"email": body.email},
    ).mappings().fetchone()

    if not otp_record:
        raise HTTPException(status_code=400, detail="No OTP found — request a new one")

    if otp_record["used_at"] is not None:
        raise HTTPException(status_code=400, detail="OTP already used")

    if otp_record["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP has expired")

    if otp_record["code_hash"] != hash_value(body.otp):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    db.execute(
        text("UPDATE app_otp_codes SET used_at = UTC_TIMESTAMP(3) WHERE id = :id"),
        {"id": otp_record["id"]},
    )

    raw_token  = generate_session_token()
    token_hash = hash_value(raw_token)
    expires_at = (
        datetime.utcnow() + timedelta(days=_SESSION_EXPIRY_DAYS)
        if body.keep_logged_in
        else datetime.utcnow() + timedelta(hours=2)
    )
    ip_address = request.client.host if request.client else None

    db.execute(
        text("""
            INSERT INTO app_sessions (user_id, token_hash, ip_address, expires_at)
            VALUES (:user_id, :token_hash, :ip, :expires_at)
        """),
        {
            "user_id":    user["id"],
            "token_hash": token_hash,
            "ip":         ip_address,
            "expires_at": expires_at,
        },
    )

    session_row = db.execute(
        text("SELECT id FROM app_sessions WHERE token_hash = :token_hash LIMIT 1"),
        {"token_hash": token_hash},
    ).mappings().fetchone()

    write_session_audit(
        db=db,
        actor_id=user["id"],
        actor_role=user.get("role"),
        action="session.login",
        session_id=session_row["id"] if session_row else None,
        ip_address=ip_address,
        org_id=user.get("organization_id"),
    )

    access_token = create_access_token(user)

    return {
        "success":      True,
        "token":        raw_token,
        "access_token": access_token,
        "expires_at":   expires_at.isoformat(),
        "user_type":    user_type,
        "user": {
            "id":              user["id"],
            "full_name":       user["full_name"],
            "email":           user["email"],
            "phone":           user["phone"],
            "organization_id": user["organization_id"],
            "role":            user["role"],
            "org_type":        user["org_type"],
        },
    }
