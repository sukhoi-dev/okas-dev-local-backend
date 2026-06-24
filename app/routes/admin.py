from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from app.db import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"], redirect_slashes=False)


# ── Request models ────────────────────────────────────────────

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    organization_id: int
    role_ids: Optional[List[int]] = []


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    organization_id: Optional[int] = None


class RoleAssign(BaseModel):
    role_id: int
    organization_id: Optional[int] = None


# ── GET /api/admin/users ──────────────────────────────────────

@router.get("/users")
def list_users(search: Optional[str] = None, org_id: Optional[int] = None):
    conditions = []
    params = []

    if search:
        conditions.append("(u.full_name LIKE %s OR u.email LIKE %s)")
        like = f"%{search}%"
        params += [like, like]
    if org_id:
        conditions.append("u.organization_id = %s")
        params.append(org_id)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    sql = f"""
        SELECT
            u.id,
            u.full_name,
            u.email,
            u.phone,
            u.active_ind,
            u.last_login_at,
            u.created_at,
            o.id      AS org_id,
            o.name    AS org_name,
            o.org_type,
            GROUP_CONCAT(r.name ORDER BY r.name SEPARATOR ',')         AS role_names,
            GROUP_CONCAT(r.display_name ORDER BY r.name SEPARATOR ',') AS role_display_names,
            GROUP_CONCAT(aur.id ORDER BY r.name SEPARATOR ',')         AS user_role_ids,
            GROUP_CONCAT(r.id ORDER BY r.name SEPARATOR ',')           AS role_ids
        FROM app_users u
        LEFT JOIN organizations o    ON o.id = u.organization_id
        LEFT JOIN app_user_roles aur ON aur.user_id = u.id
        LEFT JOIN roles r            ON r.id = aur.role_id
        {where}
        GROUP BY u.id
        ORDER BY u.created_at DESC
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    for row in rows:
        row["active_ind"] = bool(row["active_ind"])
        row["roles"] = []
        if row["role_ids"]:
            ids = row["role_ids"].split(",")
            names = row["role_names"].split(",")
            displays = row["role_display_names"].split(",")
            ur_ids = row["user_role_ids"].split(",")
            row["roles"] = [
                {"id": int(ids[i]), "name": names[i], "display_name": displays[i], "user_role_id": int(ur_ids[i])}
                for i in range(len(ids))
            ]
        del row["role_ids"], row["role_names"], row["role_display_names"], row["user_role_ids"]

    return {"success": True, "data": rows}


# ── GET /api/admin/users/{id} ─────────────────────────────────

@router.get("/users/{user_id}")
def get_user(user_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    u.id, u.full_name, u.email, u.phone, u.active_ind,
                    u.last_login_at, u.created_at, u.updated_at,
                    o.id   AS org_id,
                    o.name AS org_name
                FROM app_users u
                LEFT JOIN organizations o ON o.id = u.organization_id
                WHERE u.id = %s
            """, (user_id,))
            user = cur.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            user["active_ind"] = bool(user["active_ind"])

            cur.execute("""
                SELECT aur.id AS user_role_id, r.id, r.name, r.display_name
                FROM app_user_roles aur
                JOIN roles r ON r.id = aur.role_id
                WHERE aur.user_id = %s
            """, (user_id,))
            user["roles"] = cur.fetchall()

    return {"success": True, "data": user}


# ── POST /api/admin/users ─────────────────────────────────────

@router.post("/users", status_code=201)
def create_user(payload: UserCreate):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM app_users WHERE email = %s", (payload.email,))
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="Email already exists")

            cur.execute("""
                INSERT INTO app_users (full_name, email, phone, organization_id, active_ind)
                VALUES (%s, %s, %s, %s, 1)
            """, (payload.full_name, payload.email, payload.phone, payload.organization_id))
            user_id = cur.lastrowid

            for role_id in (payload.role_ids or []):
                cur.execute("""
                    INSERT IGNORE INTO app_user_roles (user_id, role_id, organization_id)
                    VALUES (%s, %s, %s)
                """, (user_id, role_id, payload.organization_id))

    return {"success": True, "data": {"id": user_id}}


# ── PUT /api/admin/users/{id} ─────────────────────────────────

@router.put("/users/{user_id}")
def update_user(user_id: int, payload: UserUpdate):
    fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clause = ", ".join(f"{k} = %s" for k in fields)
    params = list(fields.values()) + [user_id]

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE app_users SET {set_clause} WHERE id = %s", params)
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found")

    return {"success": True}


# ── PATCH /api/admin/users/{id}/toggle ───────────────────────

@router.patch("/users/{user_id}/toggle")
def toggle_user_status(user_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT active_ind FROM app_users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")
            new_status = 0 if row["active_ind"] else 1
            cur.execute("UPDATE app_users SET active_ind = %s WHERE id = %s", (new_status, user_id))

    return {"success": True, "data": {"active_ind": bool(new_status)}}


# ── DELETE /api/admin/users/{id} ─────────────────────────────

@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM app_users WHERE id = %s", (user_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="User not found")
            cur.execute("DELETE FROM app_users WHERE id = %s", (user_id,))


# ── POST /api/admin/users/{id}/roles ─────────────────────────

@router.post("/users/{user_id}/roles", status_code=201)
def assign_role(user_id: int, payload: RoleAssign):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM app_users WHERE id = %s", (user_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="User not found")
            cur.execute("SELECT id FROM roles WHERE id = %s", (payload.role_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Role not found")

            try:
                cur.execute("""
                    INSERT INTO app_user_roles (user_id, role_id, organization_id)
                    VALUES (%s, %s, %s)
                """, (user_id, payload.role_id, payload.organization_id))
                new_id = cur.lastrowid
            except Exception:
                raise HTTPException(status_code=409, detail="Role already assigned")

    return {"success": True, "data": {"id": new_id}}


# ── DELETE /api/admin/users/{id}/roles/{role_id} ─────────────

@router.delete("/users/{user_id}/roles/{role_id}", status_code=204)
def remove_role(user_id: int, role_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM app_user_roles WHERE user_id = %s AND role_id = %s
            """, (user_id, role_id))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Role assignment not found")


# ── GET /api/admin/roles ──────────────────────────────────────

@router.get("/roles")
def list_roles():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, display_name, description FROM roles ORDER BY id")
            rows = cur.fetchall()
    return {"success": True, "data": rows}


# ── GET /api/admin/orgs ───────────────────────────────────────

@router.get("/orgs")
def list_orgs():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, slug, email, phone, org_type
                FROM organizations
                WHERE active_ind = 1
                ORDER BY org_type, name
            """)
            rows = cur.fetchall()
    return {"success": True, "data": rows}
