from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.base import get_session
from app.models.projects import Project, ProjectOwner, ProjectMember, ProjectManagerHistory

router = APIRouter(prefix="/we-okas/projects", tags=["we-okas | projects"], redirect_slashes=False)


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class PrimaryContact(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None


class ProcessorDetails(BaseModel):
    serial_number: str


class ProjectCreate(BaseModel):
    name: str
    organization_id: int
    serial_number: str
    project_type: str = "residential"
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    notes: Optional[str] = None
    project_manager_id: Optional[int] = None
    primary_contact: Optional[PrimaryContact] = None
    processor: Optional[ProcessorDetails] = None


class ProjectUpdate(BaseModel):
    name: str
    serial_number: str
    project_type: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    notes: Optional[str] = None
    project_manager_id: Optional[int] = None
    primary_contact: Optional[PrimaryContact] = None


class ProjectPatch(BaseModel):
    name: Optional[str] = None
    serial_number: Optional[str] = None
    project_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    notes: Optional[str] = None
    project_manager_id: Optional[int] = None
    primary_contact: Optional[PrimaryContact] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

_LIST_SQL = """
    SELECT
        p.id, p.name, p.serial_number, p.project_type, p.status,
        p.address, p.city, p.state, p.pincode,
        p.installed_at, p.notes, p.active_ind,
        p.project_manager_id,
        h.full_name   AS owner_name,
        h.email       AS owner_email,
        h.phone       AS owner_phone,
        u.full_name   AS manager_name,
        ps.status     AS subscription_status,
        c.serial_number AS processor_serial_number,
        c.status        AS processor_status
    FROM projects p
    LEFT JOIN project_owners po
           ON po.project_id = p.id AND po.is_primary = 1 AND po.active_ind = 1
    LEFT JOIN homeowners h  ON h.id  = po.homeowner_id
    LEFT JOIN app_users  u  ON u.id  = p.project_manager_id
    LEFT JOIN project_subscriptions ps
           ON ps.project_id = p.id AND ps.status IN ('trial','active')
    LEFT JOIN controllers c
           ON c.project_id = p.id AND c.active_ind = 1
"""


def _serialize(row) -> dict:
    row = dict(row)
    if row.get("installed_at"):
        row["installed_at"] = row["installed_at"].isoformat()
    return row


def _check_serial_unique(db: Session, serial_number: str, exclude_id: int = None):
    if exclude_id:
        result = db.execute(
            text("SELECT id FROM projects WHERE serial_number = :sn AND id != :eid"),
            {"sn": serial_number, "eid": exclude_id},
        ).fetchone()
    else:
        result = db.execute(
            text("SELECT id FROM projects WHERE serial_number = :sn"),
            {"sn": serial_number},
        ).fetchone()
    if result:
        raise HTTPException(status_code=409, detail="serial_number already exists")


def _check_processor_serial_unique(db: Session, serial_number: str):
    result = db.execute(
        text("SELECT id FROM controllers WHERE serial_number = :sn"),
        {"sn": serial_number},
    ).fetchone()
    if result:
        raise HTTPException(status_code=409, detail="processor serial_number already exists")


# ── STORY 1 — GET /we-okas/projects  (list + search + filter) ────────────────

@router.get("")
def list_projects(
    search: Optional[str] = Query(None, description="Search by name, serial number, city or owner name"),
    status: Optional[str] = Query(None, description="Filter by project status"),
    project_type: Optional[str] = Query(None, description="Filter by project type"),
    include_archived: bool = Query(False, description="Include archived/deleted projects"),
    db: Session = Depends(get_session),
):
    conditions = []
    params = {}

    if not include_archived:
        conditions.append("p.active_ind = 1")

    if status:
        conditions.append("p.status = :status")
        params["status"] = status

    if project_type:
        conditions.append("p.project_type = :project_type")
        params["project_type"] = project_type

    if search:
        conditions.append(
            "(p.name LIKE :search OR p.serial_number LIKE :search OR p.city LIKE :search OR h.full_name LIKE :search)"
        )
        params["search"] = f"%{search}%"

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"{_LIST_SQL} {where} ORDER BY p.created_at DESC"

    rows = db.execute(text(sql), params).mappings().all()
    return {"success": True, "total": len(rows), "data": [_serialize(r) for r in rows]}


# ── STORY 1 — GET /we-okas/projects/{id}  (detail / prefill for edit) ────────

@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_session)):
    row = db.execute(
        text(f"{_LIST_SQL} WHERE p.id = :id"),
        {"id": project_id},
    ).mappings().fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    return {"success": True, "data": _serialize(row)}


# ── STORY 2 — POST /we-okas/projects  (create) ───────────────────────────────

@router.post("", status_code=201)
def create_project(body: ProjectCreate, db: Session = Depends(get_session)):
    valid_types = {"residential", "commercial", "hospitality", "retail", "other"}
    if body.project_type not in valid_types:
        raise HTTPException(status_code=422, detail=f"project_type must be one of {valid_types}")

    # 1. Validate serial number uniqueness
    _check_serial_unique(db, body.serial_number)

    # 2. Validate processor serial uniqueness if provided
    if body.processor:
        _check_processor_serial_unique(db, body.processor.serial_number)

    # 3. Insert project via ORM
    project = Project(
        organization_id=body.organization_id,
        project_manager_id=body.project_manager_id,
        name=body.name,
        serial_number=body.serial_number,
        project_type=body.project_type,
        address=body.address,
        city=body.city,
        state=body.state,
        pincode=body.pincode,
        notes=body.notes,
    )
    db.add(project)
    db.flush()
    project_id = project.id

    # 4. Create / link homeowner as primary contact
    if body.primary_contact:
        existing = db.execute(
            text("SELECT id FROM homeowners WHERE email = :email"),
            {"email": body.primary_contact.email},
        ).fetchone()

        if existing:
            homeowner_id = existing.id
        else:
            db.execute(
                text("INSERT INTO homeowners (full_name, email, phone) VALUES (:name, :email, :phone)"),
                {"name": body.primary_contact.full_name, "email": body.primary_contact.email, "phone": body.primary_contact.phone},
            )
            homeowner_id = db.execute(text("SELECT LAST_INSERT_ID() AS id")).fetchone().id

        owner = ProjectOwner(project_id=project_id, homeowner_id=homeowner_id, is_primary=True)
        db.add(owner)

    # 5. Assign project manager as project member + record history
    if body.project_manager_id:
        role = db.execute(
            text("SELECT id FROM roles WHERE name = 'project_manager' LIMIT 1")
        ).fetchone()
        if role:
            db.add(ProjectMember(
                project_id=project_id,
                user_id=body.project_manager_id,
                role_id=role.id,
                active_ind=True,
            ))
        db.add(ProjectManagerHistory(
            project_id=project_id,
            user_id=body.project_manager_id,
        ))

    # 6. Create controller (processor) entry if serial provided
    if body.processor:
        db.execute(
            text("INSERT INTO controllers (project_id, serial_number, model, status) VALUES (:pid, :sn, 'OKAS Signature', 'offline')"),
            {"pid": project_id, "sn": body.processor.serial_number},
        )

    db.flush()

    # 7. Return created project with joins
    created = db.execute(
        text(f"{_LIST_SQL} WHERE p.id = :id"),
        {"id": project_id},
    ).mappings().fetchone()

    return {"success": True, "data": _serialize(created)}


# ── STORY 3 — PUT /we-okas/projects/{id}  (full update) ──────────────────────

@router.put("/{project_id}")
def update_project(project_id: int, body: ProjectUpdate, db: Session = Depends(get_session)):
    valid_types = {"residential", "commercial", "hospitality", "retail", "other"}
    if body.project_type not in valid_types:
        raise HTTPException(status_code=422, detail=f"project_type must be one of {valid_types}")

    project = db.get(Project, project_id)
    if not project or not project.active_ind:
        raise HTTPException(status_code=404, detail="Project not found")

    _check_serial_unique(db, body.serial_number, exclude_id=project_id)

    project.name = body.name
    project.serial_number = body.serial_number
    project.project_type = body.project_type
    project.address = body.address
    project.city = body.city
    project.state = body.state
    project.pincode = body.pincode
    project.notes = body.notes
    project.project_manager_id = body.project_manager_id

    # Update primary contact if provided
    if body.primary_contact:
        owner = db.execute(
            text("SELECT homeowner_id FROM project_owners WHERE project_id = :pid AND is_primary = 1"),
            {"pid": project_id},
        ).fetchone()
        if owner:
            db.execute(
                text("UPDATE homeowners SET full_name = :name, phone = :phone WHERE id = :id"),
                {"name": body.primary_contact.full_name, "phone": body.primary_contact.phone, "id": owner.homeowner_id},
            )

    db.flush()

    updated = db.execute(
        text(f"{_LIST_SQL} WHERE p.id = :id"),
        {"id": project_id},
    ).mappings().fetchone()

    return {"success": True, "data": _serialize(updated)}


# ── STORY 3 — PATCH /we-okas/projects/{id}  (partial update) ─────────────────

@router.patch("/{project_id}")
def patch_project(project_id: int, body: ProjectPatch, db: Session = Depends(get_session)):
    project = db.get(Project, project_id)
    if not project or not project.active_ind:
        raise HTTPException(status_code=404, detail="Project not found")

    if body.serial_number and body.serial_number != project.serial_number:
        _check_serial_unique(db, body.serial_number, exclude_id=project_id)

    # Apply only provided fields
    for field in ("name", "serial_number", "project_type", "address", "city", "state", "pincode", "notes", "project_manager_id"):
        value = getattr(body, field)
        if value is not None:
            setattr(project, field, value)

    # Patch primary contact if provided
    if body.primary_contact:
        owner = db.execute(
            text("SELECT homeowner_id FROM project_owners WHERE project_id = :pid AND is_primary = 1"),
            {"pid": project_id},
        ).fetchone()
        if owner:
            updates = {}
            if body.primary_contact.full_name:
                updates["full_name"] = body.primary_contact.full_name
            if body.primary_contact.phone:
                updates["phone"] = body.primary_contact.phone
            if updates:
                set_clause = ", ".join(f"{k} = :{k}" for k in updates)
                updates["id"] = owner.homeowner_id
                db.execute(text(f"UPDATE homeowners SET {set_clause} WHERE id = :id"), updates)

    db.flush()

    patched = db.execute(
        text(f"{_LIST_SQL} WHERE p.id = :id"),
        {"id": project_id},
    ).mappings().fetchone()

    return {"success": True, "data": _serialize(patched)}


# ── STORY 4 — DELETE /we-okas/projects/{id}  (soft delete / archive) ─────────

@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_session)):
    project = db.get(Project, project_id)
    if not project or not project.active_ind:
        raise HTTPException(status_code=404, detail="Project not found")

    # Soft delete project
    project.active_ind = False

    # Revoke all member access
    db.execute(
        text("UPDATE project_members SET active_ind = 0 WHERE project_id = :pid"),
        {"pid": project_id},
    )

    # Close open PM history entry
    db.execute(
        text("""
            UPDATE project_manager_history
            SET unassigned_at = NOW(3), reason = 'project_archived'
            WHERE project_id = :pid AND unassigned_at IS NULL
        """),
        {"pid": project_id},
    )

    # Log to audit_logs
    db.execute(
        text("""
            INSERT INTO audit_logs (action, entity_type, entity_id, new_value)
            VALUES ('project.archive', 'project', :pid, :val)
        """),
        {"pid": project_id, "val": f'{{"project_id": {project_id}, "name": "{project.name}"}}'},
    )

    return {
        "success": True,
        "message": f"Project '{project.name}' has been archived. It will be retained for 45 days.",
    }


# ── STORY 4 — PATCH /we-okas/projects/{id}/restore ───────────────────────────

@router.patch("/{project_id}/restore")
def restore_project(project_id: int, db: Session = Depends(get_session)):
    project = db.get(Project, project_id)
    if not project or project.active_ind:
        raise HTTPException(status_code=404, detail="Archived project not found")

    project.active_ind = True

    # Log to audit_logs
    db.execute(
        text("""
            INSERT INTO audit_logs (action, entity_type, entity_id, new_value)
            VALUES ('project.restore', 'project', :pid, :val)
        """),
        {"pid": project_id, "val": f'{{"project_id": {project_id}, "name": "{project.name}"}}'},
    )

    db.flush()

    restored = db.execute(
        text(f"{_LIST_SQL} WHERE p.id = :id"),
        {"id": project_id},
    ).mappings().fetchone()

    return {"success": True, "data": _serialize(restored)}
