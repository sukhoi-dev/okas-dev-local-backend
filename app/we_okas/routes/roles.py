from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid

from app.auth import get_current_user
from app.db import get_orm_session
from app.models.auth import AppUser, AppUserRole, Role, RolePermission
from app.models.audit import AuditLog

router = APIRouter(
    prefix="/api/we-okas/roles",
    tags=["we-okas | roles"],
    redirect_slashes=False,
    dependencies=[Depends(get_current_user)],
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

class ProjectsPermission(BaseModel):
    scope: str = "none"

    @validator("scope")
    def validate_scope(cls, v):
        if v not in ("all_projects", "own_projects", "none"):
            raise ValueError("scope must be 'all_projects', 'own_projects', or 'none'")
        return v


class MembersPermission(BaseModel):
    create: bool = False
    view:   bool = False
    edit:   bool = False
    delete: bool = False


class DesignStudioPermission(BaseModel):
    access: bool = False


class SystemIntegratorsPermission(BaseModel):
    create: bool = False
    view:   bool = False
    edit:   bool = False
    delete: bool = False


class PermissionsBody(BaseModel):
    projects:           Optional[ProjectsPermission]           = None
    members:            Optional[MembersPermission]            = None
    design_studio:      Optional[DesignStudioPermission]       = None
    system_integrators: Optional[SystemIntegratorsPermission]  = None


class RoleCreate(BaseModel):
    name:        str
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
        if v.system_integrators and any([
            v.system_integrators.create, v.system_integrators.view,
            v.system_integrators.edit, v.system_integrators.delete,
        ]):
            has_any = True
        if not has_any:
            raise ValueError("permissions must include at least one module with a valid value")
        return v


class RoleUpdate(BaseModel):
    name:        Optional[str]           = None
    description: Optional[str]           = None
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
    member_ids:  Optional[List[int]] = None


# ── ORM helpers ──────────────────────────────────────────────────────────────

def _build_permissions(perms: List[RolePermission]) -> dict:
    """Reconstruct the structured permissions dict from ORM RolePermission objects."""
    result = {
        "projects":           {"scope": "none"},
        "members":            {"create": False, "view": False, "edit": False, "delete": False},
        "design_studio":      {"access": False},
        "system_integrators": {"create": False, "view": False, "edit": False, "delete": False},
    }
    for p in perms:
        feature, action, allowed = p.feature, p.action, bool(p.is_allowed)
        if feature == "projects" and allowed:
            result["projects"]["scope"] = action
        elif feature == "members" and action in result["members"]:
            result["members"][action] = allowed
        elif feature == "design_studio" and action == "access":
            result["design_studio"]["access"] = allowed
        elif feature == "system_integrators" and action in result["system_integrators"]:
            result["system_integrators"][action] = allowed
    return result


def _permissions_to_models(role_id: int, permissions: PermissionsBody) -> List[RolePermission]:
    """Convert a PermissionsBody into a list of RolePermission ORM objects."""
    models: List[RolePermission] = []
    if permissions.projects:
        scope = permissions.projects.scope
        if scope != "none":
            models.append(RolePermission(role_id=role_id, feature="projects", action=scope, is_allowed=True))
    if permissions.members:
        for action in ("create", "view", "edit", "delete"):
            models.append(RolePermission(
                role_id=role_id, feature="members",
                action=action, is_allowed=getattr(permissions.members, action),
            ))
    if permissions.design_studio:
        models.append(RolePermission(
            role_id=role_id, feature="design_studio",
            action="access", is_allowed=permissions.design_studio.access,
        ))
    if permissions.system_integrators:
        for action in ("create", "view", "edit", "delete"):
            models.append(RolePermission(
                role_id=role_id, feature="system_integrators",
                action=action, is_allowed=getattr(permissions.system_integrators, action),
            ))
    return models


def _fmt_role(role: Role, perms: List[RolePermission], member_count: int) -> dict:
    return {
        "id":           role.id,
        "name":         role.name,
        "description":  role.description,
        "member_count": member_count,
        "permissions":  _build_permissions(perms),
    }


def _fetch_role(db: Session, role_id: int) -> Optional[dict]:
    """Load a single role with its permissions and member count."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        return None
    perms  = db.query(RolePermission).filter(RolePermission.role_id == role_id).all()
    count  = db.query(func.count(AppUserRole.id)).filter(AppUserRole.role_id == role_id).scalar() or 0
    return _fmt_role(role, perms, count)


# ── STORY 1 — View roles ─────────────────────────────────────────────────────

@router.get("")
def list_roles(
    search: Optional[str] = Query(None),
    current_user: dict    = Depends(get_current_user),
    db: Session           = Depends(get_orm_session),
):
    org_id = current_user["organization_id"]

    # Member count per role scoped to this org
    mc_subq = (
        db.query(
            AppUserRole.role_id.label("role_id"),
            func.count(AppUserRole.id).label("cnt"),
        )
        .filter(AppUserRole.organization_id == org_id)
        .group_by(AppUserRole.role_id)
        .subquery("mc")
    )

    # Role IDs assigned to any user in this org (system/global roles)
    org_role_ids_subq = (
        db.query(AppUserRole.role_id)
        .filter(AppUserRole.organization_id == org_id)
        .distinct()
        .subquery("org_role_ids")
    )

    q = (
        db.query(Role, func.coalesce(mc_subq.c.cnt, 0).label("member_count"))
        .outerjoin(mc_subq, mc_subq.c.role_id == Role.id)
    )

    if search:
        like = f"%{search}%"
        q = q.filter(Role.name.ilike(like) | Role.description.ilike(like))

    q = q.filter(Role.name.notin_(['distributor', 'si']))
    role_rows = q.order_by(Role.id.desc()).all()

    # Fetch all permissions in one query, then group by role_id
    role_ids  = [r.id for r, _ in role_rows]
    perm_map: dict = {}
    if role_ids:
        all_perms = db.query(RolePermission).filter(RolePermission.role_id.in_(role_ids)).all()
        for p in all_perms:
            perm_map.setdefault(p.role_id, []).append(p)

    data = [
        _fmt_role(role, perm_map.get(role.id, []), count)
        for role, count in role_rows
    ]
    return _resp(200, "Roles retrieved successfully", data)


@router.get("/{role_id}/members")
def get_role_members(
    role_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session        = Depends(get_orm_session),
):
    org_id = current_user["organization_id"]
    if not db.query(Role).filter(Role.id == role_id).first():
        return _err(404, "Role not found")

    rows = (
        db.query(AppUserRole, AppUser)
        .join(AppUser, AppUser.id == AppUserRole.user_id)
        .filter(AppUserRole.role_id == role_id, AppUserRole.organization_id == org_id)
        .order_by(AppUser.full_name)
        .all()
    )

    members = [
        {
            "assignment_id": aur.id,
            "user_id":       u.id,
            "full_name":     u.full_name,
            "email":         u.email,
            "avatar_url":    u.avatar_url,
        }
        for aur, u in rows
    ]
    return _resp(200, "Role members retrieved successfully", members)


@router.get("/{role_id}")
def get_role(
    role_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session        = Depends(get_orm_session),
):
    org_id = current_user["organization_id"]
    # Verify this role belongs to the caller's org
    owns = db.query(AppUserRole).filter(
        AppUserRole.role_id == role_id,
        AppUserRole.organization_id == org_id,
    ).first()
    if not owns:
        return _err(404, "Role not found")
    role = _fetch_role(db, role_id)
    if not role:
        return _err(404, "Role not found")
    return _resp(200, "Role retrieved successfully", role)


# ── STORY 2 — Create role ────────────────────────────────────────────────────

@router.post("", status_code=201)
def create_role(
    body: RoleCreate,
    current_user: dict = Depends(get_current_user),
    db: Session        = Depends(get_orm_session),
):
    org_id = current_user["organization_id"]

    # Name uniqueness
    if db.query(Role).filter(Role.name == body.name).first():
        return _err(409, "Role name already exists")

    role = Role(name=body.name, display_name=body.name, description=body.description)
    db.add(role)
    db.flush()   # populate role.id

    for perm in _permissions_to_models(role.id, body.permissions):
        db.add(perm)

    db.add(AuditLog(
        action="role_created",
        entity_type="role",
        entity_id=role.id,
        new_value={"name": body.name},
    ))

    db.flush()
    return _resp(201, "Role created successfully", _fetch_role(db, role.id))


# ── STORY 3 — Edit role ──────────────────────────────────────────────────────

@router.put("/{role_id}")
def update_role(
    role_id: int,
    body: RoleCreate,
    current_user: dict = Depends(get_current_user),
    db: Session        = Depends(get_orm_session),
):
    org_id = current_user["organization_id"]
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        return _err(404, "Role not found")

    # Name uniqueness (skip if unchanged)
    if body.name != role.name:
        if db.query(Role).filter(
            Role.name == body.name,
            Role.id != role_id,
        ).first():
            return _err(409, "Role name already exists")

    role.name         = body.name
    role.display_name = body.name
    role.description  = body.description

    # Replace all permissions
    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete(synchronize_session=False)
    for perm in _permissions_to_models(role_id, body.permissions):
        db.add(perm)

    db.add(AuditLog(
        action="role_updated",
        entity_type="role",
        entity_id=role_id,
        new_value={"name": body.name},
    ))

    db.flush()
    return _resp(200, "Role updated successfully", _fetch_role(db, role_id))


@router.patch("/{role_id}")
def partial_update_role(
    role_id: int,
    body: RoleUpdate,
    db: Session = Depends(get_orm_session),
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        return _err(404, "Role not found")

    # Name uniqueness (only if changing)
    if body.name is not None and body.name != role.name:
        if db.query(Role).filter(Role.name == body.name, Role.id != role_id).first():
            return _err(409, "Role name already exists")

    if body.name        is not None: role.name        = body.name
    if body.description is not None: role.description = body.description

    if body.permissions is not None:
        db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
        ).delete(synchronize_session=False)
        for perm in _permissions_to_models(role_id, body.permissions):
            db.add(perm)

    db.add(AuditLog(
        action="role_patched",
        entity_type="role",
        entity_id=role_id,
    ))

    db.flush()
    return _resp(200, "Role updated successfully", _fetch_role(db, role_id))


# ── STORY 4 — Delete role ────────────────────────────────────────────────────

@router.post("/{role_id}/reassign")
def reassign_role_members(
    role_id: int,
    body: ReassignBody,
    db: Session = Depends(get_orm_session),
):
    if not db.query(Role).filter(Role.id == role_id).first():
        return _err(404, "Role not found")

    if not db.query(Role).filter(Role.id == body.new_role_id).first():
        return _err(404, "Target role not found")

    if body.new_role_id == role_id:
        return _err(400, "Cannot reassign members to the same role")

    q = db.query(AppUserRole).filter(AppUserRole.role_id == role_id)
    if body.member_ids:
        q = q.filter(AppUserRole.user_id.in_(body.member_ids))

    affected = q.update({"role_id": body.new_role_id}, synchronize_session=False)

    db.add(AuditLog(
        action="role_members_reassigned",
        entity_type="role",
        entity_id=role_id,
        new_value={"new_role_id": body.new_role_id, "affected_count": affected},
    ))

    return _resp(200, f"{affected} member(s) reassigned successfully", {"affected_count": affected})


@router.delete("/{role_id}")
def delete_role(
    role_id: int,
    db: Session = Depends(get_orm_session),
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        return _err(404, "Role not found")

    # Block deletion if members are still assigned
    member_count = (
        db.query(func.count(AppUserRole.id))
        .filter(AppUserRole.role_id == role_id)
        .scalar() or 0
    )
    if member_count > 0:
        return _err(
            409,
            f"Role has {member_count} assigned member(s). Reassign them before deleting.",
        )

    # Delete child records first (FK constraint)
    db.query(RolePermission).filter(
        RolePermission.role_id == role_id,
    ).delete(synchronize_session=False)
    db.flush()   # ensure permissions are gone before deleting the role row

    db.add(AuditLog(
        action="role_deleted",
        entity_type="role",
        entity_id=role_id,
        old_value={"name": role.name},
    ))

    db.delete(role)   # use ORM delete so identity map stays consistent

    return _resp(200, "Role deleted successfully", None)
