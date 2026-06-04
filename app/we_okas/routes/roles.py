from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from typing import Optional, List
import uuid
import json

from app.auth import get_current_user
from app.db import get_db

router = APIRouter(
    prefix="/we-okas/roles",
    tags=["we-okas | roles"],
    redirect_slashes=False,
    dependencies=[Depends(get_current_user)],
)

# ── Response helpers ─────────────────────────────────────────────────────────

def _resp(status_code: int, message: str, body=None) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "status": status_code,
        "message": message,
        "body": body,
    }


def _err(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=_resp(status_code, message, None),
    )


# ── Pydantic models ──────────────────────────────────────────────────────────

class ProjectsPermission(BaseModel):
    scope: str = "none"

    @validator("scope")
    def validate_scope(cls, v):
        if v not in ("all_projects", "own_projects", "none"):
            raise ValueError("scope must be 'all_projects', 'own_projects', or 'none'")
        return v


class MembersPermission(BaseModel):
    create: bool = False
    view: bool = False
    edit: bool = False
    delete: bool = False


class DesignStudioPermission(BaseModel):
    access: bool = False


class PermissionsBody(BaseModel):
    projects: Optional[ProjectsPermission] = None
    members: Optional[MembersPermission] = None
    design_studio: Optional[DesignStudioPermission] = None


class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: PermissionsBody

    @validator("name")
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Role name cannot be empty")
        if len(v) > 50:
            raise ValueError("Role name cannot exceed 50 characters")
        return v

    @validator("permissions")
    def validate_permissions(cls, v):
        has_any = False
        if v.projects and v.projects.scope != "none":
            has_any = True
        if v.members and any([v.members.create, v.members.view, v.members.edit, v.members.delete]):
            has_any = True
        if v.design_studio and v.design_studio.access:
            has_any = True
        if not has_any:
            raise ValueError("permissions must include at least one module with a valid value")
        return v


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[PermissionsBody] = None

    @validator("name")
    def validate_name(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Role name cannot be empty")
            if len(v) > 50:
                raise ValueError("Role name cannot exceed 50 characters")
        return v


class ReassignBody(BaseModel):
    new_role_id: int
    member_ids: Optional[List[int]] = None


# ── Internal helpers ─────────────────────────────────────────────────────────

def _permissions_to_rows(permissions: PermissionsBody) -> list:
    rows = []
    if permissions.projects:
        scope = permissions.projects.scope
        if scope != "none":
            rows.append(("projects", scope, True))
    if permissions.members:
        for action in ("create", "view", "edit", "delete"):
            rows.append(("members", action, getattr(permissions.members, action)))
    if permissions.design_studio:
        rows.append(("design_studio", "access", permissions.design_studio.access))
    return rows


def _build_permissions(perm_rows: list) -> dict:
    result = {
        "projects": {"scope": "none"},
        "members": {"create": False, "view": False, "edit": False, "delete": False},
        "design_studio": {"access": False},
    }
    for row in perm_rows:
        feature, action, is_allowed = row["feature"], row["action"], bool(row["is_allowed"])
        if feature == "projects" and is_allowed:
            result["projects"]["scope"] = action
        elif feature == "members" and action in result["members"]:
            result["members"][action] = is_allowed
        elif feature == "design_studio" and action == "access":
            result["design_studio"]["access"] = is_allowed
    return result


def _fetch_role_row(cur, role_id: int):
    cur.execute(
        """
        SELECT r.id, r.name, r.description, r.created_at,
               COUNT(DISTINCT aur.id) AS member_count
        FROM roles r
        LEFT JOIN app_user_roles aur ON aur.role_id = r.id
        WHERE r.id = %s
        GROUP BY r.id, r.name, r.description, r.created_at
        """,
        (role_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    cur.execute(
        "SELECT feature, action, is_allowed FROM role_permissions WHERE role_id = %s",
        (role_id,),
    )
    perm_rows = cur.fetchall()
    if row.get("created_at"):
        row["created_at"] = row["created_at"].isoformat()
    row["permissions"] = _build_permissions(perm_rows)
    return row


# ── STORY 1 — View roles ─────────────────────────────────────────────────────

@router.get("")
def list_roles(search: Optional[str] = Query(None)):
    with get_db() as conn:
        with conn.cursor() as cur:
            if search:
                cur.execute(
                    """
                    SELECT r.id, r.name, r.description, r.created_at,
                           COUNT(DISTINCT aur.id) AS member_count
                    FROM roles r
                    LEFT JOIN app_user_roles aur ON aur.role_id = r.id
                    WHERE r.name LIKE %s OR r.description LIKE %s
                    GROUP BY r.id, r.name, r.description, r.created_at
                    ORDER BY r.created_at DESC
                    """,
                    (f"%{search}%", f"%{search}%"),
                )
            else:
                cur.execute(
                    """
                    SELECT r.id, r.name, r.description, r.created_at,
                           COUNT(DISTINCT aur.id) AS member_count
                    FROM roles r
                    LEFT JOIN app_user_roles aur ON aur.role_id = r.id
                    GROUP BY r.id, r.name, r.description, r.created_at
                    ORDER BY r.created_at DESC
                    """
                )
            rows = cur.fetchall()

            role_ids = [r["id"] for r in rows]
            perm_map: dict = {}
            if role_ids:
                placeholders = ",".join(["%s"] * len(role_ids))
                cur.execute(
                    f"SELECT role_id, feature, action, is_allowed "
                    f"FROM role_permissions WHERE role_id IN ({placeholders})",
                    role_ids,
                )
                for pr in cur.fetchall():
                    perm_map.setdefault(pr["role_id"], []).append(pr)

            for r in rows:
                if r.get("created_at"):
                    r["created_at"] = r["created_at"].isoformat()
                r["permissions"] = _build_permissions(perm_map.get(r["id"], []))

    return _resp(200, "Roles retrieved successfully", rows)


@router.get("/{role_id}/members")
def get_role_members(role_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM roles WHERE id = %s", (role_id,))
            if not cur.fetchone():
                return _err(404, "Role not found")

            cur.execute(
                """
                SELECT aur.id AS assignment_id,
                       u.id AS user_id, u.full_name, u.email, u.avatar_url
                FROM app_user_roles aur
                JOIN app_users u ON u.id = aur.user_id
                WHERE aur.role_id = %s
                ORDER BY u.full_name
                """,
                (role_id,),
            )
            members = cur.fetchall()

    return _resp(200, "Role members retrieved successfully", members)


@router.get("/{role_id}")
def get_role(role_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            role = _fetch_role_row(cur, role_id)
    if not role:
        return _err(404, "Role not found")
    return _resp(200, "Role retrieved successfully", role)


# ── STORY 2 — Create role ────────────────────────────────────────────────────

@router.post("", status_code=201)
def create_role(body: RoleCreate):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM roles WHERE name = %s", (body.name,))
            if cur.fetchone():
                return _err(409, "Role name already exists")

            cur.execute(
                "INSERT INTO roles (name, description) VALUES (%s, %s)",
                (body.name, body.description),
            )
            role_id = cur.lastrowid

            for feature, action, is_allowed in _permissions_to_rows(body.permissions):
                cur.execute(
                    "INSERT INTO role_permissions (role_id, feature, action, is_allowed) "
                    "VALUES (%s, %s, %s, %s)",
                    (role_id, feature, action, is_allowed),
                )

            cur.execute(
                "INSERT INTO audit_logs (action, entity_type, entity_id, new_value) "
                "VALUES (%s, %s, %s, %s)",
                ("role_created", "role", role_id, json.dumps({"name": body.name})),
            )

            role = _fetch_role_row(cur, role_id)

    return _resp(201, "Role created successfully", role)


# ── STORY 3 — Edit role ──────────────────────────────────────────────────────

@router.put("/{role_id}")
def update_role(role_id: int, body: RoleCreate):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM roles WHERE id = %s", (role_id,))
            existing = cur.fetchone()
            if not existing:
                return _err(404, "Role not found")

            if body.name != existing["name"]:
                cur.execute(
                    "SELECT id FROM roles WHERE name = %s AND id != %s",
                    (body.name, role_id),
                )
                if cur.fetchone():
                    return _err(409, "Role name already exists")

            cur.execute(
                "UPDATE roles SET name = %s, description = %s WHERE id = %s",
                (body.name, body.description, role_id),
            )

            cur.execute("DELETE FROM role_permissions WHERE role_id = %s", (role_id,))
            for feature, action, is_allowed in _permissions_to_rows(body.permissions):
                cur.execute(
                    "INSERT INTO role_permissions (role_id, feature, action, is_allowed) "
                    "VALUES (%s, %s, %s, %s)",
                    (role_id, feature, action, is_allowed),
                )

            cur.execute(
                "INSERT INTO audit_logs (action, entity_type, entity_id, new_value) "
                "VALUES (%s, %s, %s, %s)",
                ("role_updated", "role", role_id, json.dumps({"name": body.name})),
            )

            role = _fetch_role_row(cur, role_id)

    return _resp(200, "Role updated successfully", role)


@router.patch("/{role_id}")
def partial_update_role(role_id: int, body: RoleUpdate):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, description FROM roles WHERE id = %s", (role_id,)
            )
            existing = cur.fetchone()
            if not existing:
                return _err(404, "Role not found")

            new_name = body.name if body.name is not None else existing["name"]
            new_desc = body.description if body.description is not None else existing["description"]

            if body.name is not None and body.name != existing["name"]:
                cur.execute(
                    "SELECT id FROM roles WHERE name = %s AND id != %s",
                    (body.name, role_id),
                )
                if cur.fetchone():
                    return _err(409, "Role name already exists")

            cur.execute(
                "UPDATE roles SET name = %s, description = %s WHERE id = %s",
                (new_name, new_desc, role_id),
            )

            if body.permissions is not None:
                cur.execute("DELETE FROM role_permissions WHERE role_id = %s", (role_id,))
                for feature, action, is_allowed in _permissions_to_rows(body.permissions):
                    cur.execute(
                        "INSERT INTO role_permissions (role_id, feature, action, is_allowed) "
                        "VALUES (%s, %s, %s, %s)",
                        (role_id, feature, action, is_allowed),
                    )

            cur.execute(
                "INSERT INTO audit_logs (action, entity_type, entity_id) VALUES (%s, %s, %s)",
                ("role_patched", "role", role_id),
            )

            role = _fetch_role_row(cur, role_id)

    return _resp(200, "Role updated successfully", role)


# ── STORY 4 — Delete role ────────────────────────────────────────────────────

@router.post("/{role_id}/reassign")
def reassign_role_members(role_id: int, body: ReassignBody):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM roles WHERE id = %s", (role_id,))
            if not cur.fetchone():
                return _err(404, "Role not found")

            cur.execute("SELECT id FROM roles WHERE id = %s", (body.new_role_id,))
            if not cur.fetchone():
                return _err(404, "Target role not found")

            if body.new_role_id == role_id:
                return _err(400, "Cannot reassign members to the same role")

            member_ids = body.member_ids or None

            if member_ids:
                placeholders = ",".join(["%s"] * len(member_ids))
                cur.execute(
                    f"UPDATE app_user_roles SET role_id = %s "
                    f"WHERE role_id = %s AND user_id IN ({placeholders})",
                    [body.new_role_id, role_id] + list(member_ids),
                )
            else:
                cur.execute(
                    "UPDATE app_user_roles SET role_id = %s WHERE role_id = %s",
                    (body.new_role_id, role_id),
                )
            affected = cur.rowcount

            cur.execute(
                "INSERT INTO audit_logs (action, entity_type, entity_id, new_value) "
                "VALUES (%s, %s, %s, %s)",
                (
                    "role_members_reassigned",
                    "role",
                    role_id,
                    json.dumps({"new_role_id": body.new_role_id, "affected_count": affected}),
                ),
            )

    return _resp(200, f"{affected} member(s) reassigned successfully", {"affected_count": affected})


@router.delete("/{role_id}")
def delete_role(role_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM roles WHERE id = %s", (role_id,))
            if not cur.fetchone():
                return _err(404, "Role not found")

            cur.execute(
                "SELECT COUNT(*) AS cnt FROM app_user_roles WHERE role_id = %s", (role_id,)
            )
            cnt = cur.fetchone()["cnt"]
            if cnt > 0:
                return _err(
                    409,
                    f"Role has {cnt} assigned member(s). Reassign them before deleting.",
                )

            cur.execute("DELETE FROM role_permissions WHERE role_id = %s", (role_id,))
            cur.execute("DELETE FROM roles WHERE id = %s", (role_id,))

            cur.execute(
                "INSERT INTO audit_logs (action, entity_type, entity_id) VALUES (%s, %s, %s)",
                ("role_deleted", "role", role_id),
            )

    return _resp(200, "Role deleted successfully", None)
