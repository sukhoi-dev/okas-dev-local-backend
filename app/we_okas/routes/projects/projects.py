from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import uuid

from app.auth import get_current_user
from app.db import get_orm_session
from app.models.projects import Project, ProjectManagerHistory, ProjectOwner, ProjectMember
from app.models.auth import Homeowner, AppUserRole, Organization, AppUser
from app.models.audit import AuditLog

router = APIRouter(
    prefix="/api/we-okas/projects",
    tags=["we-okas | projects"],
    redirect_slashes=False,
)

_VALID_TYPES   = {"residential", "commercial", "hospitality", "retail", "other"}
_VALID_STATUS  = {"active", "inactive", "under_maintenance", "completed"}


# ── Response helpers ──────────────────────────────────────────────────────────

def _resp(status_code: int, message: str, body=None) -> dict:
    return {"id": str(uuid.uuid4()), "status": status_code, "message": message, "body": body}


def _err(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=_resp(status_code, message))


# ── validation Schema ────────────────────────────────────────────────────────────────────

class HomeownerInput(BaseModel):
    email:           str
    full_name:       Optional[str] = None
    phone:           Optional[str] = None
    preferred_login: Optional[str] = "otp"

    @field_validator("email")
    @classmethod
    def email_required(cls, v):
        if not v.strip():
            raise ValueError("homeowner email cannot be empty")
        return v.strip().lower()

    @field_validator("preferred_login")
    @classmethod
    def valid_login(cls, v):
        if v and v not in {"google", "otp"}:
            raise ValueError("preferred_login must be 'google' or 'otp'")
        return v


class ProjectCreate(BaseModel):
    name:                    str
    project_type:            str
    homeowner:               HomeownerInput
    organization_id:         Optional[int] = None
    serial_number:           Optional[str] = None
    status:                  Optional[str] = "active"
    project_manager_id:      Optional[int] = None
    location_id:             Optional[int] = None
    address:                 Optional[str] = None
    city:                    Optional[str] = None
    state:                   Optional[str] = None
    country:                 Optional[str] = None
    pincode:                 Optional[str] = None
    notes:                   Optional[str] = None
    installed_at:            Optional[datetime] = None
    project_metadata:        Optional[dict] = None

    @field_validator("name")
    @classmethod
    def name_required(cls, v):
        if not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @field_validator("project_type")
    @classmethod
    def valid_type(cls, v):
        if v not in _VALID_TYPES:
            raise ValueError(f"project_type must be one of {sorted(_VALID_TYPES)}")
        return v

    @field_validator("status")
    @classmethod
    def valid_status(cls, v):
        if v and v not in _VALID_STATUS:
            raise ValueError(f"status must be one of {sorted(_VALID_STATUS)}")
        return v

    @field_validator("project_manager_id", mode="before")
    @classmethod
    def coerce_manager_id(cls, v):
        if v is not None:
            try:
                return int(v)
            except (ValueError, TypeError):
                raise ValueError("project_manager_id must be a valid integer")
        return v


# ── response Format ────────────────────────────────────────────────────────────────────

def _fmt(p: Project) -> dict:
    return {
        "id":                 p.id,
        "name":               p.name,
        "organization_id":    p.organization_id,
        "project_type":       p.project_type,
        "serial_number":      p.serial_number,
        "status":             p.status,
        "project_manager_id": p.project_manager_id,
        "location_id":        p.location_id,
        "address":            p.address,
        "city":               p.city,
        "state":              p.state,
        "country":            p.country,
        "pincode":            p.pincode,
        "notes":              p.notes,
        "installed_at":       p.installed_at.isoformat() if p.installed_at else None,
        "project_metadata":   p.project_metadata,
        "created_at":         p.created_at.isoformat() if p.created_at else None,
        "updated_at":         p.updated_at.isoformat() if p.updated_at else None,
    }


# ── POST /we-okas/projects ────────────────────────────────────────────────────

def _fmt_homeowner(h: Homeowner) -> dict:
    return {
        "id":        h.id,
        "email":     h.email,
        "full_name": h.full_name,
        "phone":     h.phone,
    }


@router.post("", status_code=201)
def create_project(
    body:         ProjectCreate,
    current_user: dict    = Depends(get_current_user),
    db:           Session = Depends(get_orm_session)
):
    # TODO: replace with current_user["organization_id"] once auth is enabled
    _DEFAULT_ORG_ID = 1
    organization_id = body.organization_id or _DEFAULT_ORG_ID

    # Duplicate name check within the same organization
    if db.query(Project).filter(
        Project.name == body.name,
        Project.organization_id == organization_id,
        Project.active_ind == True,
    ).first():
        return _err(409, f"A project named '{body.name}' already exists")

    # Duplicate serial number check
    if body.serial_number:
        if db.query(Project).filter(Project.serial_number == body.serial_number).first():
            return _err(409, f"Serial number '{body.serial_number}' is already in use")

    # ── 1. Homeowner: find existing or create ─────────────────────────────────
    hw_in = body.homeowner
    homeowner = db.query(Homeowner).filter(Homeowner.email == hw_in.email).first()
    if homeowner is None:
        homeowner = Homeowner(
            email           = hw_in.email,
            full_name       = hw_in.full_name,
            phone           = hw_in.phone,
            preferred_login = hw_in.preferred_login or "otp",
            active_ind      = True,
        )
        db.add(homeowner)
        try:
            db.flush()
        except IntegrityError as e:
            db.rollback()
            return _err(400, "Failed to create homeowner: " + str(e.orig))

    # ── 2. Project ────────────────────────────────────────────────────────────
    project = Project(
        organization_id    = organization_id,
        project_manager_id = body.project_manager_id,
        location_id        = body.location_id,
        name               = body.name,
        serial_number      = body.serial_number,
        project_type       = body.project_type,
        status             = body.status or "active",
        address            = body.address,
        city               = body.city,
        state              = body.state,
        country            = body.country,
        pincode            = body.pincode,
        notes              = body.notes,
        installed_at       = body.installed_at,
        project_metadata   = body.project_metadata,
        active_ind         = True,
        updated_by         = current_user["user_id"],
    )
    db.add(project)
    try:
        db.flush()
    except IntegrityError as e:
        db.rollback()
        orig = str(e.orig)
        if "fk_proj_org" in orig or "organization_id" in orig:
            return _err(400, f"organization_id {organization_id} does not exist")
        if "fk_proj_manager" in orig or "project_manager_id" in orig:
            return _err(400, f"project_manager_id {body.project_manager_id} does not exist")
        if "fk_proj_location" in orig or "location_id" in orig:
            return _err(400, f"location_id {body.location_id} does not exist")
        return _err(400, "Database integrity error: " + orig)

    # ── 3. ProjectOwner: link homeowner as primary owner ──────────────────────
    db.add(ProjectOwner(
        project_id   = project.id,
        homeowner_id = homeowner.id,
        is_primary   = True,
        active_ind   = True,
    ))

    # ── 4. ProjectMember + history: add project manager ───────────────────────
    if body.project_manager_id:
        user_role = db.query(AppUserRole).filter(
            AppUserRole.user_id         == body.project_manager_id,
            AppUserRole.organization_id == organization_id,
        ).first()

        if user_role:
            db.add(ProjectMember(
                project_id  = project.id,
                user_id     = body.project_manager_id,
                role_id     = user_role.role_id,
                assigned_by = current_user["user_id"],
                active_ind  = True,
            ))

        db.add(ProjectManagerHistory(
            project_id  = project.id,
            user_id     = body.project_manager_id,
            assigned_by = current_user["user_id"],
        ))

    db.add(AuditLog(
        action          = "project.created",
        entity_type     = "project",
        entity_id       = project.id,
        organization_id = organization_id,
        project_id      = project.id,
        new_value       = _fmt(project),
        user_id=current_user["user_id"],
    ))

    return _resp(201, "Project created successfully", {
        **_fmt(project),
        "homeowner": _fmt_homeowner(homeowner),
    })


# ── GET /we-okas/projects ─────────────────────────────────────────────────────

def _base_project_query(db: Session):
    return (
        db.query(Project, Homeowner, AppUser)
        .outerjoin(
            ProjectOwner,
            and_(
                ProjectOwner.project_id == Project.id,
                ProjectOwner.is_primary == True,
                ProjectOwner.active_ind == True,
            ),
        )
        .outerjoin(Homeowner, Homeowner.id == ProjectOwner.homeowner_id)
        .outerjoin(AppUser, AppUser.id == Project.project_manager_id)
    )


def _fmt_row(row) -> dict:
    project: Project               = row[0]
    homeowner: Optional[Homeowner] = row[1]
    manager: Optional[AppUser]     = row[2]
    return {
        **_fmt(project),
        "owner": _fmt_homeowner(homeowner) if homeowner else None,
        "assigned_member": {
            "id":        manager.id,
            "full_name": manager.full_name,
        } if manager else None,
    }


@router.get("", status_code=200)
def list_projects(
    status:       Optional[str] = Query(None),
    project_type: Optional[str] = Query(None),
    page:         int           = Query(1, ge=1),
    page_size:    int           = Query(20, ge=1, le=100),
    current_user: dict          = Depends(get_current_user),
    db:           Session       = Depends(get_orm_session),
):
    if status and status not in _VALID_STATUS:
        return _err(400, f"status must be one of {sorted(_VALID_STATUS)}")
    if project_type and project_type not in _VALID_TYPES:
        return _err(400, f"project_type must be one of {sorted(_VALID_TYPES)}")

    organization_id = current_user["organization_id"]
    org_type = current_user.get("org_type")

    if org_type == "distributor":
        si_org_ids = [
            row.id for row in db.query(Organization.id).filter(
                Organization.parent_organization_id == organization_id,
                Organization.org_type == "si",
                Organization.active_ind == True,
            ).all()
        ]
        visible_org_ids = si_org_ids + [organization_id]
        q = _base_project_query(db).filter(
            Project.active_ind == True,
            Project.organization_id.in_(visible_org_ids),
        )
    else:
        q = _base_project_query(db).filter(
            Project.active_ind == True,
            Project.organization_id == organization_id,
        )
        if org_type == "member":
            q = q.filter(Project.project_manager_id == current_user["user_id"])

    if status:
        q = q.filter(Project.status == status)
    if project_type:
        q = q.filter(Project.project_type == project_type)

    total = q.count()
    rows  = q.order_by(Project.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return _resp(200, "Projects fetched successfully", {
        "total":     total,
        "page":      page,
        "page_size": page_size,
        "projects":  [_fmt_row(r) for r in rows],
    })


# ── GET /we-okas/projects/{project_id} ───────────────────────────────────────

@router.get("/{project_id}", status_code=200)
def get_project(
    project_id:   int,
    current_user: dict    = Depends(get_current_user),
    db:           Session = Depends(get_orm_session),
):
    organization_id = current_user["organization_id"]
    org_type        = current_user.get("org_type")

    q = _base_project_query(db).filter(
        Project.id         == project_id,
        Project.active_ind == True,
    )

    if org_type == "distributor":
        si_org_ids = [
            row.id for row in db.query(Organization.id).filter(
                Organization.parent_organization_id == organization_id,
                Organization.org_type == "si",
                Organization.active_ind == True,
            ).all()
        ]
        visible_org_ids = si_org_ids + [organization_id]
        q = q.filter(Project.organization_id.in_(visible_org_ids))
    else:
        q = q.filter(Project.organization_id == organization_id)
        if org_type == "member":
            q = q.filter(Project.project_manager_id == current_user["user_id"])

    row = q.first()
    if not row:
        return _err(404, f"Project {project_id} not found")

    return _resp(200, "Project fetched successfully", _fmt_row(row))


# ── PATCH /we-okas/projects/{project_id} ─────────────────────────────────────

class HomeownerUpdate(BaseModel):
    email:      Optional[str] = None
    full_name:  Optional[str] = None
    phone:      Optional[str] = None

    @field_validator("email")
    @classmethod
    def email_strip(cls, v):
        return v.strip().lower() if v else v


class ProjectUpdate(BaseModel):
    name:               Optional[str]           = None
    project_type:       Optional[str]           = None
    serial_number:      Optional[str]           = None
    status:             Optional[str]           = None
    project_manager_id: Optional[int]           = None
    location_id:        Optional[int]           = None
    address:            Optional[str]           = None
    city:               Optional[str]           = None
    state:              Optional[str]           = None
    country:            Optional[str]           = None
    pincode:            Optional[str]           = None
    notes:              Optional[str]           = None
    installed_at:       Optional[datetime]      = None
    homeowner:          Optional[HomeownerUpdate] = None
    project_metadata:   Optional[dict]           = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip() if v else v

    @field_validator("project_type")
    @classmethod
    def valid_type(cls, v):
        if v and v not in _VALID_TYPES:
            raise ValueError(f"project_type must be one of {sorted(_VALID_TYPES)}")
        return v

    @field_validator("status")
    @classmethod
    def valid_status(cls, v):
        if v and v not in _VALID_STATUS:
            raise ValueError(f"status must be one of {sorted(_VALID_STATUS)}")
        return v

    @field_validator("project_manager_id", mode="before")
    @classmethod
    def coerce_manager_id(cls, v):
        if v is not None:
            try:
                return int(v)
            except (ValueError, TypeError):
                raise ValueError("project_manager_id must be a valid integer")
        return v


@router.patch("/{project_id}", status_code=200)
def update_project(
    project_id: int,
    body:       ProjectUpdate,
    current_user: dict = Depends(get_current_user),
    db:         Session = Depends(get_orm_session),
):
    project = db.query(Project).filter(Project.id == project_id, Project.active_ind == True).first()
    if not project:
        return _err(404, f"Project {project_id} not found")

    if body.name is not None:
        if db.query(Project).filter(
            Project.name == body.name,
            Project.organization_id == project.organization_id,
            Project.active_ind == True,
            Project.id != project_id,
        ).first():
            return _err(409, f"A project named '{body.name}' already exists in this organization")
        project.name = body.name

    if body.serial_number is not None:
        if db.query(Project).filter(
            Project.serial_number == body.serial_number,
            Project.id != project_id,
        ).first():
            return _err(409, f"Serial number '{body.serial_number}' is already in use")
        project.serial_number = body.serial_number

    old_manager_id = project.project_manager_id

    for field in ("project_type", "status", "project_manager_id", "location_id",
                  "address", "city", "state", "country", "pincode", "notes", "installed_at",
                  "project_metadata"):
        val = getattr(body, field)
        if val is not None:
            setattr(project, field, val)

    project.updated_by = current_user["user_id"]

    try:
        db.flush()
    except IntegrityError as e:
        db.rollback()
        orig = str(e.orig)
        if "fk_proj_manager" in orig or "project_manager_id" in orig:
            return _err(400, f"project_manager_id {body.project_manager_id} does not exist")
        if "fk_proj_location" in orig or "location_id" in orig:
            return _err(400, f"location_id {body.location_id} does not exist")
        return _err(400, "Database integrity error: " + orig)

    # ── ProjectMember + history when manager changes ──────────────────────────
    if body.project_manager_id and body.project_manager_id != old_manager_id:
        user_role = db.query(AppUserRole).filter(
            AppUserRole.user_id         == body.project_manager_id,
            AppUserRole.organization_id == project.organization_id,
        ).first()

        if user_role:
            # deactivate previous member entry for old manager
            if old_manager_id:
                db.query(ProjectMember).filter(
                    ProjectMember.project_id == project.id,
                    ProjectMember.user_id    == old_manager_id,
                    ProjectMember.active_ind == True,
                ).update({"active_ind": False}, synchronize_session=False)

            db.add(ProjectMember(
                project_id  = project.id,
                user_id     = body.project_manager_id,
                role_id     = user_role.role_id,
                assigned_by = current_user["user_id"],
                active_ind  = True,
            ))

        db.add(ProjectManagerHistory(
            project_id  = project.id,
            user_id     = body.project_manager_id,
            assigned_by = current_user["user_id"],
        ))

    # ── Homeowner update ──────────────────────────────────────────────────────
    project_owner = db.query(ProjectOwner).filter(
        ProjectOwner.project_id == project.id,
        ProjectOwner.is_primary == True,
        ProjectOwner.active_ind == True,
    ).first()
    homeowner = db.query(Homeowner).filter(
        Homeowner.id == project_owner.homeowner_id
    ).first() if project_owner else None

    if body.homeowner:
        hw = body.homeowner
        if project_owner and homeowner:
            email_changed = hw.email and hw.email != homeowner.email
            if email_changed:
                # email changed — check if new email belongs to another homeowner
                existing = db.query(Homeowner).filter(Homeowner.email == hw.email).first()
                if existing and existing.id != homeowner.id:
                    # reassign ProjectOwner to the existing homeowner with new email
                    project_owner.homeowner_id = existing.id
                    homeowner = existing
                else:
                    homeowner.email = hw.email
            if hw.full_name is not None: homeowner.full_name = hw.full_name
            if hw.phone     is not None: homeowner.phone     = hw.phone
        else:
            # no primary owner yet — find by email or create, then link
            if hw.email:
                homeowner = db.query(Homeowner).filter(Homeowner.email == hw.email).first()
                if homeowner is None:
                    homeowner = Homeowner(
                        email      = hw.email,
                        full_name  = hw.full_name,
                        phone      = hw.phone,
                        active_ind = True,
                    )
                    db.add(homeowner)
                    db.flush()
                db.add(ProjectOwner(
                    project_id   = project.id,
                    homeowner_id = homeowner.id,
                    is_primary   = True,
                    active_ind   = True,
                ))

    # ── AuditLog ──────────────────────────────────────────────────────────────
    db.add(AuditLog(
        action          = "project.updated",
        entity_type     = "project",
        entity_id       = project.id,
        organization_id = project.organization_id,
        project_id      = project.id,
        new_value       = _fmt(project),
        user_id=current_user["user_id"],
    ))

    return _resp(200, "Project updated successfully", {
        **_fmt(project),
        "homeowner": _fmt_homeowner(homeowner) if homeowner else None,
    })
