import os
import time
import boto3
import requests
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr
from app.db import get_db
from app.auth import create_access_token

PRODUCTION_API = "https://api.okas.ai"

router = APIRouter(prefix="/api/auth", tags=["auth"], redirect_slashes=False)

SSM_PARAM   = "/okas/super_admins"
AWS_REGION  = os.getenv("AWS_REGION", "ap-south-1")

# Simple in-process cache so we don't hit SSM on every login (5-minute TTL)
_super_admin_cache: dict = {"emails": set(), "fetched_at": 0.0}
_CACHE_TTL = 300  # seconds


def _get_super_admins() -> set:
    now = time.time()
    if now - _super_admin_cache["fetched_at"] < _CACHE_TTL:
        return _super_admin_cache["emails"]

    try:
        ssm = boto3.client("ssm", region_name=AWS_REGION)
        resp = ssm.get_parameter(Name=SSM_PARAM)
        emails = {e.strip().lower() for e in resp["Parameter"]["Value"].split(",") if e.strip()}
    except Exception:
        # Fall back to env var for local dev, or keep stale cache if SSM is unreachable
        fallback = os.getenv("SUPER_ADMIN_EMAILS", "")
        emails = {e.strip().lower() for e in fallback.split(",") if e.strip()} \
                 or _super_admin_cache["emails"]

    _super_admin_cache["emails"] = emails
    _super_admin_cache["fetched_at"] = now
    return emails


class VerifyRequest(BaseModel):
    email: EmailStr


@router.post("/verify")
def verify_user(payload: VerifyRequest):
    """
    Called after Cognito callback. Checks access in two tiers:
      1. Super admin list (SSM /okas/super_admins) — bypasses app_users entirely.
      2. app_users table — must exist and be active.
    Returns is_super_admin so the frontend can enable the /admin route.
    """
    email_lower = payload.email.lower()
    super_admins = _get_super_admins()

    if email_lower in super_admins:
        # Super admins may or may not be in app_users — always let them through
        _stamp_last_login_if_exists(email_lower)
        access_token = create_access_token({
            "id":              0,
            "email":           payload.email,
            "full_name":       "Super Admin",
            "organization_id": None,
            "role":            "super_admin",
            "org_type":        None,
        })
        return {
            "success":      True,
            "access_token": access_token,
            "data": {
                "email":          payload.email,
                "is_super_admin": True,
            },
        }

    # Regular user — must be in app_users
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    u.id,
                    u.full_name,
                    u.email,
                    u.phone,
                    u.active_ind,
                    u.organization_id,
                    o.name AS org_name,
                    o.org_type,
                    GROUP_CONCAT(r.name ORDER BY r.name SEPARATOR ',') AS roles
                FROM app_users u
                LEFT JOIN organizations o    ON o.id = u.organization_id
                LEFT JOIN app_user_roles aur ON aur.user_id = u.id
                LEFT JOIN roles r            ON r.id = aur.role_id
                WHERE u.email = %s
                GROUP BY u.id
            """, (email_lower,))
            user = cur.fetchone()

    if not user:
        raise HTTPException(status_code=403, detail="no_access")

    if not user["active_ind"]:
        raise HTTPException(status_code=403, detail="account_disabled")

    # Determine org_type: if the login email exists in organizations.email
    # the user is a distributor/si; otherwise treat as member
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM organizations WHERE email = %s LIMIT 1",
                (email_lower,)
            )
            org_email_row = cur.fetchone()

    org_type = user["org_type"] if org_email_row and user["org_type"] in ("distributor", "si") else "member"

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE app_users SET last_login_at = NOW(3) WHERE id = %s",
                (user["id"],)
            )

    roles_list = user["roles"].split(",") if user["roles"] else []
    role       = roles_list[0] if roles_list else None

    user["active_ind"]    = bool(user["active_ind"])
    user["is_super_admin"] = False
    user["roles"]          = roles_list

    access_token = create_access_token({
        "id":              user["id"],
        "email":           user["email"],
        "full_name":       user["full_name"],
        "organization_id": user["organization_id"],
        "role":            role,
        "org_type":        org_type,
    })

    return {
        "success":      True,
        "access_token": access_token,
        "data": user,
        "user": {
            "id":              user["id"],
            "full_name":       user["full_name"],
            "email":           user["email"],
            "phone":           user["phone"],
            "organization_id": user["organization_id"],
            "role":            role,
            "org_type":        org_type,
            "is_super_admin":  False,
        },
    }


@router.get("/verify-otp")
def verify_otp_proxy(
    email: str = Query(..., description="User email"),
    otp: str = Query(..., description="OTP code"),
    keep_logged_in: bool = Query(False),
):
    try:
        resp = requests.post(
            f"{PRODUCTION_API}/api/auth/verify-otp",
            json={"email": email, "otp": otp, "keep_logged_in": keep_logged_in},
            timeout=10,
        )
        prod_data = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to reach production API: {exc}")

    if not prod_data.get("success"):
        return {"success": False, "message": prod_data.get("message", "Verification failed")}

    email_lower = prod_data.get("data", {}).get("email", "").lower()

    # Fetch full user record + role
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.id, u.full_name, u.email, u.organization_id,
                       r.name AS role
                FROM app_users u
                LEFT JOIN app_user_roles aur ON aur.user_id = u.id
                LEFT JOIN roles r            ON r.id = aur.role_id
                WHERE u.email = %s
                LIMIT 1
            """, (email_lower,))
            user = cur.fetchone()

    if not user:
        return {"success": False, "message": "User not found"}

    # Determine org_type
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT org_type FROM organizations WHERE email = %s LIMIT 1",
                (email_lower,)
            )
            org_row = cur.fetchone()

    org_type = org_row["org_type"] if org_row and org_row["org_type"] in ("distributor", "si") else "member"

    user["org_type"] = org_type
    access_token = create_access_token(user)

    return {
        "success":         True,
        "org_type":        org_type,
        "email":           email_lower,
        "organization_id": user["organization_id"],
        "access_token":    access_token,
    }


def _stamp_last_login_if_exists(email: str):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE app_users SET last_login_at = NOW(3) WHERE email = %s",
                    (email,)
                )
    except Exception:
        pass  # super admin may not be in app_users — that's fine
