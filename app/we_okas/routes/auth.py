import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

from app.auth import create_access_token, get_current_user, _TTL_H
from app.db import get_db

router = APIRouter(prefix="/api/we-okas/auth", tags=["we-okas | auth"], redirect_slashes=False)

_JWT_TTL_SECONDS = _TTL_H * 3600


def _resp(status_code: int, message: str, body=None) -> dict:
    return {
        "id":      str(uuid.uuid4()),
        "status":  status_code,
        "message": message,
        "body":    body,
    }


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class TokenRequest(BaseModel):
    email: EmailStr


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch_user_with_context(conn, email: str) -> Optional[dict]:
    """Fetch user row joined with org + latest role."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.id, u.email, u.full_name, u.organization_id,
                   u.active_ind,
                   r.id   AS role_id,
                   r.name AS role_name,
                   o.name AS org_name,
                   o.slug AS org_slug
            FROM app_users u
            LEFT JOIN app_user_roles aur ON aur.user_id = u.id
            LEFT JOIN roles r             ON r.id = aur.role_id
            LEFT JOIN organizations o     ON o.id = u.organization_id
            WHERE u.email = %s
            ORDER BY aur.id DESC
            LIMIT 1
            """,
            (str(email),),
        )
        return cur.fetchone()


def _fetch_permissions(conn, user_id: int) -> List[str]:
    """Return list of 'feature.action' strings the user is allowed."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT rp.feature, rp.action
            FROM app_user_roles aur
            JOIN role_permissions rp ON rp.role_id = aur.role_id
            WHERE aur.user_id = %s AND rp.is_allowed = TRUE
            """,
            (user_id,),
        )
        rows = cur.fetchall()
    return [f"{r['feature']}.{r['action']}" for r in rows]


def _build_login_response(user: dict) -> dict:
    token = create_access_token(user)
    return _resp(
        200,
        "Login successful",
        {
            "access_token": token,
            "token_type":   "bearer",
            "expires_in":   _JWT_TTL_SECONDS,
            "user": {
                "id":              user["id"],
                "email":           user["email"],
                "full_name":       user["full_name"],
                "organization_id": user["organization_id"],
                "org_name":        user.get("org_name"),
                "org_slug":        user.get("org_slug"),
                "role": (
                    {"id": user["role_id"], "name": user["role_name"]}
                    if user.get("role_id") else None
                ),
            },
        },
    )


# ── GET /we-okas/auth/me  (current user + permissions) ───────────────────────

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """
    Returns the authenticated user's profile and their permission set.
    Use to refresh the frontend auth state after page reload.
    """
    with get_db() as conn:
        user = _fetch_user_with_context(conn, current_user["sub"])
        if not user or not user["active_ind"]:
            return JSONResponse(
                status_code=401,
                content=_resp(401, "User not found or inactive", None),
            )

    return _resp(
        200,
        "User retrieved successfully",
        {
            "user": {
                "id":              user["id"],
                "email":           user["email"],
                "full_name":       user["full_name"],
                "organization_id": user["organization_id"],
                "org_name":        user.get("org_name"),
                "org_slug":        user.get("org_slug"),
                "role": (
                    {"id": user["role_id"], "name": user["role_name"]}
                    if user.get("role_id") else None
                ),
            },
        },
    )


# ── GET /we-okas/auth/permissions  (full permission set for current user) ─────

@router.get("/permissions")
def get_permissions(current_user: dict = Depends(get_current_user)):
    """
    Returns the authenticated user's full permission set.
    Hit this immediately after login to populate the frontend permission store.
    """
    with get_db() as conn:
        user = _fetch_user_with_context(conn, current_user["sub"])
        if not user or not user["active_ind"]:
            return JSONResponse(
                status_code=401,
                content=_resp(401, "User not found or inactive", None),
            )

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT rp.feature, rp.action, rp.is_allowed
                FROM app_user_roles aur
                JOIN role_permissions rp ON rp.role_id = aur.role_id
                WHERE aur.user_id = %s
                ORDER BY rp.feature, rp.action
                """,
                (user["id"],),
            )
            rows = cur.fetchall()

    flat: List[str] = []
    grouped: dict = {}
    for r in rows:
        if r["is_allowed"]:
            key = f"{r['feature']}.{r['action']}"
            flat.append(key)
            grouped.setdefault(r["feature"], []).append(r["action"])

    return _resp(
        200,
        "Permissions retrieved successfully",
        {
            "user_id": user["id"],
            "role": (
                {"id": user["role_id"], "name": user["role_name"]}
                if user.get("role_id") else None
            ),
            "permissions": {
                "flat":    flat,
                "grouped": grouped,
            },
        },
    )


# ── POST /we-okas/auth/token  (dev-only: email without password) ──────────────

@router.post("/token")
def get_token(body: TokenRequest):
    """
    **DEV / TESTING ONLY** — issues a JWT by email alone, no password required.
    Use /login for production flows.
    """
    with get_db() as conn:
        user = _fetch_user_with_context(conn, body.email)
        if not user:
            return JSONResponse(
                status_code=404,
                content=_resp(404, "User not found or inactive", None),
            )

        if not user["active_ind"]:
            return JSONResponse(
                status_code=403,
                content=_resp(403, "Account is inactive. Contact your administrator.", None),
            )

    return _build_login_response(user)
