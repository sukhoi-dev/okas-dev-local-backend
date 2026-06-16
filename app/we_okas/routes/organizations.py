import logging
import re
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import require_permission
from app.db import get_orm_session
from app.models.auth import AppUser, AppUserRole, Organization, Role

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/we-okas/organizations",
    tags=["we-okas | organizations"],
    redirect_slashes=False,
)


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class AdminUserCreate(BaseModel):
    full_name: str
    email:     EmailStr

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("full_name cannot be empty")
        return v


class OrgCreate(BaseModel):
    name:       str
    email:      Optional[EmailStr]        = None
    phone:      Optional[str]             = None
    address:    Optional[str]             = None
    logo_url:   Optional[str]             = None
    admin_user: Optional[AdminUserCreate] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        return v


class OrgUpdate(BaseModel):
    name:       Optional[str]             = None
    email:      Optional[EmailStr]        = None
    phone:      Optional[str]             = None
    address:    Optional[str]             = None
    logo_url:   Optional[str]             = None
    status:     Optional[str]             = None
    admin_user: Optional[AdminUserCreate] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in ("active", "inactive"):
            raise ValueError("status must be 'active' or 'inactive'")
        return v


# ── Helpers ───────────────────────────────────────────────────────────────────

def _resp(status_code: int, message: str, body=None) -> dict:
    return {"id": str(uuid.uuid4()), "status": status_code, "message": message, "body": body}

def _err(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=_resp(status_code, message))

def _slug(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "org"

def _fmt(org: Organization, member_count: int = 0) -> dict:
    return {
        "id":           org.id,
        "name":         org.name,
        "slug":         org.slug,
        "email":        org.email,
        "phone":        org.phone,
        "address":      org.address,
        "logo_url":     org.logo_url,
        "status":       "active" if org.active_ind else "inactive",
        "member_count": member_count,
        "created_at":   org.created_at.isoformat() if org.created_at else None,
        "updated_at":   org.updated_at.isoformat() if org.updated_at else None,
    }

def _insert_admin_user(db: Session, org_id: int, admin: AdminUserCreate) -> dict:
    admin_role = db.query(Role).filter(Role.name == "Admin").first()
    if not admin_role:
        raise ValueError("'Admin' role not found — run scripts/seed_demo.py first")

    user = AppUser(
        organization_id=org_id,
        email=str(admin.email),
        full_name=admin.full_name.strip(),
        active_ind=True,
    )
    db.add(user)
    db.flush()
    db.add(AppUserRole(user_id=user.id, role_id=admin_role.id, organization_id=org_id))
    db.flush()
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": "Admin"}


# ── GET /we-okas/organizations ────────────────────────────────────────────────

@router.get("")
def list_organizations(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="active | inactive | all"),
    current_user: dict    = Depends(require_permission("organizations", "manage")),
    db: Session           = Depends(get_orm_session),
):
    member_counts = (
        db.query(AppUser.organization_id.label("org_id"), func.count(AppUser.id).label("cnt"))
        .filter(AppUser.active_ind == True)
        .group_by(AppUser.organization_id)
        .subquery("mc")
    )
    q = (
        db.query(Organization, func.coalesce(member_counts.c.cnt, 0).label("member_count"))
        .outerjoin(member_counts, member_counts.c.org_id == Organization.id)
    )
    if status == "inactive":
        q = q.filter(Organization.active_ind == False)
    elif status != "all":
        q = q.filter(Organization.active_ind == True)

    if search:
        like = f"%{search}%"
        q = q.filter(Organization.name.ilike(like) | Organization.email.ilike(like) | Organization.phone.ilike(like))

    rows = q.order_by(Organization.created_at.desc()).all()
    return _resp(200, "Organisations retrieved successfully", [_fmt(r[0], r[1]) for r in rows])


# ── POST /we-okas/organizations ───────────────────────────────────────────────

@router.post("", status_code=201)
def create_organization(
    body: OrgCreate,
    current_user: dict = Depends(require_permission("organizations", "manage")),
    db: Session        = Depends(get_orm_session),
):
    base_slug = _slug(body.name)
    slug, suffix = base_slug, 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    if body.admin_user:
        if db.query(AppUser).filter(AppUser.email == str(body.admin_user.email)).first():
            return _err(409, f"Email {body.admin_user.email} is already registered")

    org = Organization(
        name=body.name.strip(), slug=slug,
        email=str(body.email) if body.email else None,
        phone=body.phone, address=body.address, logo_url=body.logo_url,
        active_ind=True,
    )
    db.add(org)
    db.flush()

    admin_info = None
    if body.admin_user:
        admin_info = _insert_admin_user(db, org.id, body.admin_user)

    result = _fmt(org, 1 if admin_info else 0)
    if admin_info:
        result["admin_user"] = admin_info
    return _resp(201, "Organisation created successfully", result)


# ── PUT /we-okas/organizations/{id} ──────────────────────────────────────────

@router.put("/{org_id}")
def update_organization(
    org_id: int,
    body: OrgUpdate,
    current_user: dict = Depends(require_permission("organizations", "manage")),
    db: Session        = Depends(get_orm_session),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return _err(404, "Organisation not found")

    if body.name     is not None: org.name      = body.name.strip() or org.name
    if body.email    is not None: org.email      = str(body.email) if body.email else None
    if body.phone    is not None: org.phone      = body.phone
    if body.address  is not None: org.address    = body.address
    if body.logo_url is not None: org.logo_url   = body.logo_url
    if body.status   is not None: org.active_ind = (body.status == "active")

    admin_info = None
    if body.admin_user:
        if db.query(AppUser).filter(AppUser.email == str(body.admin_user.email)).first():
            return _err(409, f"Email {body.admin_user.email} is already registered")
        admin_info = _insert_admin_user(db, org_id, body.admin_user)

    member_count = (
        db.query(func.count(AppUser.id))
        .filter(AppUser.organization_id == org_id, AppUser.active_ind == True)
        .scalar()
    ) or 0

    db.flush()
    result = _fmt(org, member_count)
    if admin_info:
        result["admin_user"] = admin_info
    return _resp(200, "Organisation updated successfully", result)


# ── DELETE /we-okas/organizations/{id}  (soft delete) ────────────────────────

@router.delete("/{org_id}")
def deactivate_organization(
    org_id: int,
    current_user: dict = Depends(require_permission("organizations", "manage")),
    db: Session        = Depends(get_orm_session),
):
    org = db.query(Organization).filter(Organization.id == org_id, Organization.active_ind == True).first()
    if not org:
        return _err(404, "Organisation not found or already inactive")

    org.active_ind = False
    db.query(AppUser).filter(
        AppUser.organization_id == org_id, AppUser.active_ind == True
    ).update({"active_ind": False}, synchronize_session=False)

    return _resp(200, "Organisation deactivated successfully", None)
