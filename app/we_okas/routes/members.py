from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
import uuid
import json

from app.auth import require_permission
from app.db import get_db

router = APIRouter(
    prefix="/we-okas/members",
    tags=["we-okas | members"],
    redirect_slashes=False,
)


# ── Response helpers ─────────────────────────────────────────────────────────

def _resp(status_code: int, message: str, body=None) -> dict:
    return {
        "id":      str(uuid.uuid4()),
        "status":  status_code,
        "message": message,
        "body":    body,
    }


def _err(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=_resp(status_code, message, None),
    )


# ── Pydantic models ──────────────────────────────────────────────────────────

class MemberCreate(BaseModel):
    full_name:               str
    email:                   EmailStr
    phone:                   Optional[str]  = None
    role_id:                 int
    organization_id:         int
    status:                  str            = "active"
    has_design_studio_access: Optional[bool] = None   # informational; derived from role in responses

    @validator("full_name")
    def validate_full_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("full_name cannot be empty")
        return v

    @validator("status")
    def validate_status(cls, v):
        if v not in ("active", "inactive"):
            raise ValueError("status must be 'active' or 'inactive'")
        return v


class MemberUpdate(BaseModel):
    full_name:               Optional[str]      = None
    email:                   Optional[EmailStr] = None
    phone:                   Optional[str]      = None
    role_id:                 Optional[int]      = None
    status:                  Optional[str]      = None
    has_design_studio_access: Optional[bool]    = None

    @validator("status")
    def validate_status(cls, v):
        if v is not None and v not in ("active", "inactive"):
            raise ValueError("status must be 'active' or 'inactive'")
        return v


# ── SQL base select ──────────────────────────────────────────────────────────
# Fetches one row per user by anchoring to MAX(aur.id) — the latest role
# assignment — so duplicate rows never appear even if a user had multiple
# historical role entries.

_SELECT = """
    SELECT
        u.id, u.full_name, u.email, u.phone,
        u.organization_id, u.active_ind,
        CASE WHEN u.active_ind = 1 THEN 'active' ELSE 'inactive' END AS status,
        u.created_at, u.updated_at,
        r.id   AS role_id,
        r.name AS role_name,
        COALESCE(rp_ds.is_allowed, FALSE) AS has_design_studio_access
    FROM app_users u
    LEFT JOIN app_user_roles aur
           ON aur.user_id = u.id
          AND aur.id = (SELECT MAX(a2.id) FROM app_user_roles a2 WHERE a2.user_id = u.id)
    LEFT JOIN roles r ON r.id = aur.role_id
    LEFT JOIN role_permissions rp_ds
           ON rp_ds.role_id = aur.role_id
          AND rp_ds.feature = 'design_studio'
          AND rp_ds.action  = 'access'
"""


def _fmt(row: dict) -> dict:
    if not row:
        return None
    return {
        "id":                     row["id"],
        "full_name":              row["full_name"],
        "email":                  row["email"],
        "phone":                  row["phone"],
        "organization_id":        row["organization_id"],
        "status":                 row["status"],
        "has_design_studio_access": bool(row["has_design_studio_access"]),
        "role": (
            {"id": row["role_id"], "name": row["role_name"]}
            if row.get("role_id") else None
        ),
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
    }


# ── STORY 1 — View members ───────────────────────────────────────────────────

@router.get("")
def list_members(
    search: Optional[str] = Query(None, description="Filter by name or email"),
    role:   Optional[str] = Query(None, description="Filter by role name or ID"),
    status: Optional[str] = Query(None, description="active | inactive | all (default: active)"),
    current_user: dict = Depends(require_permission("members", "view")),
):
    conditions: list = []
    params:     list = []

    # status filter — default to active only
    if status == "inactive":
        conditions.append("u.active_ind = 0")
    elif status == "all":
        pass  # no active_ind filter
    else:
        conditions.append("u.active_ind = 1")

    if search:
        conditions.append("(u.full_name LIKE %s OR u.email LIKE %s)")
        params += [f"%{search}%", f"%{search}%"]

    if role:
        conditions.append("(r.name = %s OR r.id = %s)")
        params += [role, int(role) if role.isdigit() else -1]

    where  = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql    = f"{_SELECT} {where} ORDER BY u.created_at DESC"

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    return _resp(200, "Members retrieved successfully", [_fmt(r) for r in rows])


@router.get("/{member_id}")
def get_member(
    member_id: int,
    current_user: dict = Depends(require_permission("members", "view")),
):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(f"{_SELECT} WHERE u.id = %s", (member_id,))
            row = cur.fetchone()
    if not row:
        return _err(404, "Member not found")
    return _resp(200, "Member retrieved successfully", _fmt(row))


# ── STORY 2 — Create member ──────────────────────────────────────────────────

@router.post("", status_code=201)
def create_member(
    body: MemberCreate,
    current_user: dict = Depends(require_permission("members", "create")),
):
    with get_db() as conn:
        with conn.cursor() as cur:
            # email uniqueness
            cur.execute("SELECT id FROM app_users WHERE email = %s", (body.email,))
            if cur.fetchone():
                return _err(409, "Email address is already registered")

            # valid role
            cur.execute("SELECT id FROM roles WHERE id = %s", (body.role_id,))
            if not cur.fetchone():
                return _err(404, "Role not found")

            active_ind = 1 if body.status == "active" else 0

            cur.execute(
                """
                INSERT INTO app_users (organization_id, full_name, email, phone, active_ind)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (body.organization_id, body.full_name, body.email, body.phone, active_ind),
            )
            member_id = cur.lastrowid

            cur.execute(
                "INSERT INTO app_user_roles (user_id, role_id, organization_id) VALUES (%s, %s, %s)",
                (member_id, body.role_id, body.organization_id),
            )

            cur.execute(
                "INSERT INTO audit_logs (actor_id, action, entity_type, entity_id, new_value) "
                "VALUES (%s, %s, %s, %s, %s)",
                (
                    current_user["user_id"],
                    "member_created",
                    "app_user",
                    member_id,
                    json.dumps({"email": body.email, "role_id": body.role_id}),
                ),
            )

            cur.execute(f"{_SELECT} WHERE u.id = %s", (member_id,))
            created = cur.fetchone()

    return _resp(201, "Member created successfully", _fmt(created))


# ── STORY 3 — Edit member ────────────────────────────────────────────────────

@router.put("/{member_id}")
def update_member(
    member_id: int,
    body: MemberCreate,
    current_user: dict = Depends(require_permission("members", "edit")),
):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email, organization_id FROM app_users WHERE id = %s",
                (member_id,),
            )
            existing = cur.fetchone()
            if not existing:
                return _err(404, "Member not found")

            # email uniqueness check (skip if unchanged)
            if body.email.lower() != existing["email"].lower():
                cur.execute(
                    "SELECT id FROM app_users WHERE email = %s AND id != %s",
                    (body.email, member_id),
                )
                if cur.fetchone():
                    return _err(409, "Email address is already registered")

            # valid role
            cur.execute("SELECT id FROM roles WHERE id = %s", (body.role_id,))
            if not cur.fetchone():
                return _err(404, "Role not found")

            active_ind = 1 if body.status == "active" else 0

            cur.execute(
                """
                UPDATE app_users
                SET full_name = %s, email = %s, phone = %s,
                    organization_id = %s, active_ind = %s, updated_by = %s
                WHERE id = %s
                """,
                (
                    body.full_name, body.email, body.phone,
                    body.organization_id, active_ind,
                    current_user["user_id"], member_id,
                ),
            )

            # replace role assignment within the organisation
            cur.execute(
                "DELETE FROM app_user_roles WHERE user_id = %s AND organization_id = %s",
                (member_id, body.organization_id),
            )
            cur.execute(
                "INSERT INTO app_user_roles (user_id, role_id, organization_id) VALUES (%s, %s, %s)",
                (member_id, body.role_id, body.organization_id),
            )

            cur.execute(
                "INSERT INTO audit_logs (actor_id, action, entity_type, entity_id, new_value) "
                "VALUES (%s, %s, %s, %s, %s)",
                (
                    current_user["user_id"],
                    "member_updated",
                    "app_user",
                    member_id,
                    json.dumps({"email": body.email, "role_id": body.role_id}),
                ),
            )

            cur.execute(f"{_SELECT} WHERE u.id = %s", (member_id,))
            updated = cur.fetchone()

    return _resp(200, "Member updated successfully", _fmt(updated))


@router.patch("/{member_id}")
def partial_update_member(
    member_id: int,
    body: MemberUpdate,
    current_user: dict = Depends(require_permission("members", "edit")),
):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, full_name, email, phone, organization_id, active_ind "
                "FROM app_users WHERE id = %s",
                (member_id,),
            )
            existing = cur.fetchone()
            if not existing:
                return _err(404, "Member not found")

            # resolve new values — fall back to existing if not provided
            new_name   = body.full_name if body.full_name is not None else existing["full_name"]
            new_email  = str(body.email) if body.email is not None else existing["email"]
            new_phone  = body.phone if body.phone is not None else existing["phone"]
            new_active = (
                (1 if body.status == "active" else 0)
                if body.status is not None
                else existing["active_ind"]
            )

            # email uniqueness (only if changing)
            if body.email is not None and new_email.lower() != existing["email"].lower():
                cur.execute(
                    "SELECT id FROM app_users WHERE email = %s AND id != %s",
                    (new_email, member_id),
                )
                if cur.fetchone():
                    return _err(409, "Email address is already registered")

            # role validation (only if changing)
            if body.role_id is not None:
                cur.execute("SELECT id FROM roles WHERE id = %s", (body.role_id,))
                if not cur.fetchone():
                    return _err(404, "Role not found")

            cur.execute(
                """
                UPDATE app_users
                SET full_name = %s, email = %s, phone = %s,
                    active_ind = %s, updated_by = %s
                WHERE id = %s
                """,
                (new_name, new_email, new_phone, new_active, current_user["user_id"], member_id),
            )

            if body.role_id is not None:
                cur.execute(
                    "DELETE FROM app_user_roles WHERE user_id = %s AND organization_id = %s",
                    (member_id, existing["organization_id"]),
                )
                cur.execute(
                    "INSERT INTO app_user_roles (user_id, role_id, organization_id) VALUES (%s, %s, %s)",
                    (member_id, body.role_id, existing["organization_id"]),
                )

            cur.execute(
                "INSERT INTO audit_logs (actor_id, action, entity_type, entity_id) VALUES (%s, %s, %s, %s)",
                (current_user["user_id"], "member_patched", "app_user", member_id),
            )

            cur.execute(f"{_SELECT} WHERE u.id = %s", (member_id,))
            updated = cur.fetchone()

    return _resp(200, "Member updated successfully", _fmt(updated))


# ── STORY 4 — Soft-delete member ─────────────────────────────────────────────

@router.delete("/{member_id}")
def delete_member(
    member_id: int,
    current_user: dict = Depends(require_permission("members", "delete")),
):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email FROM app_users WHERE id = %s AND active_ind = 1",
                (member_id,),
            )
            existing = cur.fetchone()
            if not existing:
                return _err(404, "Member not found or already inactive")

            # soft-delete: deactivate user
            cur.execute(
                "UPDATE app_users SET active_ind = 0, updated_by = %s WHERE id = %s",
                (current_user["user_id"], member_id),
            )

            # revoke all project memberships
            cur.execute(
                "UPDATE project_members SET active_ind = 0 WHERE user_id = %s",
                (member_id,),
            )

            # invalidate all active sessions
            cur.execute("DELETE FROM app_sessions WHERE user_id = %s", (member_id,))

            cur.execute(
                "INSERT INTO audit_logs (actor_id, action, entity_type, entity_id, old_value) "
                "VALUES (%s, %s, %s, %s, %s)",
                (
                    current_user["user_id"],
                    "member_deleted",
                    "app_user",
                    member_id,
                    json.dumps({"email": existing["email"]}),
                ),
            )

    return _resp(200, "Member deactivated successfully", None)
