from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid

from app.auth import require_permission
from app.db import get_orm_session
from app.models.auth import AppUser, AppUserRole, Role, RolePermission, AppSession
from app.models.audit import AuditLog
from app.models.projects import ProjectMember

router = APIRouter(
    prefix="/api/we-okas/members",
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


# ── ORM query helpers ────────────────────────────────────────────────────────

def _member_query(db: Session):
    """
    Base SQLAlchemy query returning tuples of (AppUser, Role|None, is_allowed|None).

    Strategy: find the latest AppUserRole per user via a GROUP-BY subquery, then
    left-join outward to Role and RolePermission (design_studio.access only).
    This guarantees exactly one row per AppUser, matching the original SQL logic.
    """
    # Subquery: latest AppUserRole.id for each user_id
    latest_aur = (
        db.query(
            AppUserRole.user_id.label("user_id"),
            func.max(AppUserRole.id).label("max_id"),
        )
        .group_by(AppUserRole.user_id)
        .subquery("latest_aur")
    )

    return (
        db.query(AppUser, Role, RolePermission.is_allowed)
        .outerjoin(latest_aur, latest_aur.c.user_id == AppUser.id)
        .outerjoin(AppUserRole, AppUserRole.id == latest_aur.c.max_id)
        .outerjoin(Role, Role.id == AppUserRole.role_id)
        .outerjoin(
            RolePermission,
            (RolePermission.role_id == AppUserRole.role_id)
            & (RolePermission.feature == "design_studio")
            & (RolePermission.action  == "access"),
        )
    )


def _fmt(row) -> dict:
    """Format a (AppUser, Role|None, is_allowed|None) tuple into the API response shape."""
    user: AppUser          = row[0]
    role: Optional[Role]   = row[1]
    has_ds                 = row[2]
    return {
        "id":                     user.id,
        "full_name":              user.full_name,
        "email":                  user.email,
        "phone":                  user.phone,
        "organization_id":        user.organization_id,
        "status":                 "active" if user.active_ind else "inactive",
        "has_design_studio_access": bool(has_ds) if has_ds is not None else False,
        "role": {"id": role.id, "name": role.name} if role else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


# ── STORY 1 — View members ───────────────────────────────────────────────────

@router.get("")
def list_members(
    search: Optional[str] = Query(None, description="Filter by name or email"),
    role:   Optional[str] = Query(None, description="Filter by role name or ID"),
    status: Optional[str] = Query(None, description="active | inactive | all (default: active)"),
    current_user: dict    = Depends(require_permission("members", "view")),
    db: Session           = Depends(get_orm_session),
):
    q = _member_query(db).filter(AppUser.organization_id == current_user["organization_id"])

    # Status filter — default to active only
    if status == "inactive":
        q = q.filter(AppUser.active_ind == False)
    elif status == "all":
        pass
    else:
        q = q.filter(AppUser.active_ind == True)

    if search:
        like = f"%{search}%"
        q = q.filter(AppUser.full_name.ilike(like) | AppUser.email.ilike(like))

    if role:
        if role.isdigit():
            q = q.filter(Role.id == int(role))
        else:
            q = q.filter(Role.name == role)

    rows = q.order_by(AppUser.created_at.desc()).all()
    return _resp(200, "Members retrieved successfully", [_fmt(r) for r in rows])


@router.get("/{member_id}")
def get_member(
    member_id: int,
    current_user: dict = Depends(require_permission("members", "view")),
    db: Session        = Depends(get_orm_session),
):
    row = _member_query(db).filter(
        AppUser.id == member_id,
        AppUser.organization_id == current_user["organization_id"],
    ).first()
    if not row:
        return _err(404, "Member not found")
    return _resp(200, "Member retrieved successfully", _fmt(row))


# ── STORY 2 — Create member ──────────────────────────────────────────────────

@router.post("", status_code=201)
def create_member(
    body: MemberCreate,
    current_user: dict = Depends(require_permission("members", "create")),
    db: Session        = Depends(get_orm_session),
):
    # Validate: email uniqueness
    if db.query(AppUser).filter(AppUser.email == str(body.email)).first():
        return _err(409, "Email address is already registered")

    # Validate: role exists
    if not db.query(Role).filter(Role.id == body.role_id).first():
        return _err(404, "Role not found")

    # Create user
    user = AppUser(
        organization_id=body.organization_id,
        full_name=body.full_name,
        email=str(body.email),
        phone=body.phone,
        active_ind=(body.status == "active"),
    )
    db.add(user)
    db.flush()   # get user.id before related inserts

    # Assign role
    db.add(AppUserRole(
        user_id=user.id,
        role_id=body.role_id,
        organization_id=body.organization_id,
    ))

    # Audit
    db.add(AuditLog(
        actor_id=current_user["user_id"],
        action="member_created",
        entity_type="app_user",
        entity_id=user.id,
        new_value={"email": str(body.email), "role_id": body.role_id},
    ))

    db.flush()   # make new rows visible in the same session before SELECT
    row = _member_query(db).filter(AppUser.id == user.id).first()
    return _resp(201, "Member created successfully", _fmt(row))


# ── STORY 3 — Edit member ────────────────────────────────────────────────────

@router.put("/{member_id}")
def update_member(
    member_id: int,
    body: MemberCreate,
    current_user: dict = Depends(require_permission("members", "edit")),
    db: Session        = Depends(get_orm_session),
):
    user = db.query(AppUser).filter(AppUser.id == member_id).first()
    if not user:
        return _err(404, "Member not found")

    # Email uniqueness (only if changing)
    if str(body.email).lower() != user.email.lower():
        if db.query(AppUser).filter(
            AppUser.email == str(body.email),
            AppUser.id    != member_id,
        ).first():
            return _err(409, "Email address is already registered")

    # Role exists
    if not db.query(Role).filter(Role.id == body.role_id).first():
        return _err(404, "Role not found")

    # Update user fields
    user.full_name       = body.full_name
    user.email           = str(body.email)
    user.phone           = body.phone
    user.organization_id = body.organization_id
    user.active_ind      = (body.status == "active")
    user.updated_by      = current_user["user_id"]

    # Replace role assignment within the organisation
    db.query(AppUserRole).filter(
        AppUserRole.user_id        == member_id,
        AppUserRole.organization_id == body.organization_id,
    ).delete(synchronize_session=False)

    db.add(AppUserRole(
        user_id=member_id,
        role_id=body.role_id,
        organization_id=body.organization_id,
    ))

    # Audit
    db.add(AuditLog(
        actor_id=current_user["user_id"],
        action="member_updated",
        entity_type="app_user",
        entity_id=member_id,
        new_value={"email": str(body.email), "role_id": body.role_id},
    ))

    db.flush()
    row = _member_query(db).filter(AppUser.id == member_id).first()
    return _resp(200, "Member updated successfully", _fmt(row))


@router.patch("/{member_id}")
def partial_update_member(
    member_id: int,
    body: MemberUpdate,
    current_user: dict = Depends(require_permission("members", "edit")),
    db: Session        = Depends(get_orm_session),
):
    user = db.query(AppUser).filter(AppUser.id == member_id).first()
    if not user:
        return _err(404, "Member not found")

    # Email uniqueness (only if changing)
    if body.email is not None and str(body.email).lower() != user.email.lower():
        if db.query(AppUser).filter(
            AppUser.email == str(body.email),
            AppUser.id    != member_id,
        ).first():
            return _err(409, "Email address is already registered")

    # Role validation (only if changing)
    if body.role_id is not None:
        if not db.query(Role).filter(Role.id == body.role_id).first():
            return _err(404, "Role not found")

    # Apply only provided fields
    if body.full_name is not None: user.full_name  = body.full_name.strip()
    if body.email     is not None: user.email      = str(body.email)
    if body.phone     is not None: user.phone      = body.phone
    if body.status    is not None: user.active_ind = (body.status == "active")
    user.updated_by = current_user["user_id"]

    # Replace role assignment only if role_id was supplied
    if body.role_id is not None:
        db.query(AppUserRole).filter(
            AppUserRole.user_id        == member_id,
            AppUserRole.organization_id == user.organization_id,
        ).delete(synchronize_session=False)

        db.add(AppUserRole(
            user_id=member_id,
            role_id=body.role_id,
            organization_id=user.organization_id,
        ))

    # Audit
    db.add(AuditLog(
        actor_id=current_user["user_id"],
        action="member_patched",
        entity_type="app_user",
        entity_id=member_id,
    ))

    db.flush()
    row = _member_query(db).filter(AppUser.id == member_id).first()
    return _resp(200, "Member updated successfully", _fmt(row))


# ── STORY 4 — Soft-delete member ─────────────────────────────────────────────

@router.delete("/{member_id}")
def delete_member(
    member_id: int,
    current_user: dict = Depends(require_permission("members", "delete")),
    db: Session        = Depends(get_orm_session),
):
    user = db.query(AppUser).filter(
        AppUser.id        == member_id,
        AppUser.active_ind == True,
    ).first()
    if not user:
        return _err(404, "Member not found or already inactive")

    # Soft-delete: deactivate user record
    user.active_ind = False
    user.updated_by = current_user["user_id"]

    # Revoke all project memberships
    db.query(ProjectMember).filter(
        ProjectMember.user_id == member_id,
    ).update({"active_ind": False}, synchronize_session=False)

    # Invalidate all active sessions
    db.query(AppSession).filter(
        AppSession.user_id == member_id,
    ).delete(synchronize_session=False)

    # Audit
    db.add(AuditLog(
        actor_id=current_user["user_id"],
        action="member_deleted",
        entity_type="app_user",
        entity_id=member_id,
        old_value={"email": user.email},
    ))

    return _resp(200, "Member deactivated successfully", None)
