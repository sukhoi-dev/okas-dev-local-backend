from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from typing import Optional
from sqlalchemy.orm import Session
import uuid

from app.auth import get_current_user
from app.db import get_orm_session
from app.models.projects import Project
from app.models.auth import Organization
from app.models.location import Floor

router = APIRouter(
    prefix="/api/we-okas/projects/{project_id}/floors",
    tags=["design-studio | floors"],
    redirect_slashes=False,
)


def _resp(status_code: int, message: str, body=None) -> dict:
    return {"id": str(uuid.uuid4()), "status": status_code, "message": message, "body": body}


def _err(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=_resp(status_code, message))


def _fmt(f: Floor) -> dict:
    return {
        "id":             f.id,
        "project_id":     f.project_id,
        "floor_name":     f.name,
        "floor_pos":      f.floor_number,
        "floor_description": f.short_code,
        "floor_plan_url": f.floor_plan_url,
        "display_order":  f.display_order,
        "created_at":     f.created_at.isoformat() if f.created_at else None,
        "updated_at":     f.updated_at.isoformat() if f.updated_at else None,
    }


def _visible_project(db: Session, project_id: int, current_user: dict) -> Optional[Project]:
    organization_id = current_user["organization_id"]
    org_type        = current_user.get("org_type")

    q = db.query(Project).filter(Project.id == project_id, Project.active_ind == True)

    if org_type == "distributor":
        si_org_ids = [
            row.id for row in db.query(Organization.id).filter(
                Organization.parent_organization_id == organization_id,
                Organization.org_type == "si",
                Organization.active_ind == True,
            ).all()
        ]
        q = q.filter(Project.organization_id.in_(si_org_ids + [organization_id]))
    else:
        q = q.filter(Project.organization_id == organization_id)
        if org_type == "member":
            q = q.filter(Project.project_manager_id == current_user["user_id"])

    return q.first()


class FloorCreate(BaseModel):
    floor_name:        str
    floor_pos:          int = 0
    floor_description:  Optional[str] = None

    @field_validator("floor_name")
    @classmethod
    def name_required(cls, v):
        if not v.strip():
            raise ValueError("floor_name cannot be empty")
        return v.strip()


class FloorUpdate(BaseModel):
    floor_name:        Optional[str] = None
    floor_pos:         Optional[int] = None
    floor_description: Optional[str] = None

    @field_validator("floor_name")
    @classmethod
    def name_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("floor_name cannot be empty")
        return v.strip() if v else v


# ── GET /we-okas/projects/{project_id}/floors ─────────────────────────────────

@router.get("", status_code=200)
def list_floors(
    project_id:   int,
    current_user: dict    = Depends(get_current_user),
    db:           Session = Depends(get_orm_session),
):
    if not _visible_project(db, project_id, current_user):
        return _err(404, f"Project {project_id} not found")

    floors = (
        db.query(Floor)
        .filter(Floor.project_id == project_id, Floor.active_ind == True)
        .order_by(Floor.display_order, Floor.floor_number)
        .all()
    )
    return _resp(200, "Floors fetched successfully", {"floors": [_fmt(f) for f in floors]})


# ── POST /we-okas/projects/{project_id}/floors ────────────────────────────────

@router.post("", status_code=201)
def create_floor(
    project_id:   int,
    body:         FloorCreate,
    current_user: dict    = Depends(get_current_user),
    db:           Session = Depends(get_orm_session),
):
    if not _visible_project(db, project_id, current_user):
        return _err(404, f"Project {project_id} not found")

    next_order = (
        db.query(Floor)
        .filter(Floor.project_id == project_id, Floor.active_ind == True)
        .count()
    )

    floor = Floor(
        project_id     = project_id,
        name           = body.floor_name,
        floor_number   = body.floor_pos,
        short_code     = body.floor_description,
        display_order  = next_order,
        active_ind     = True,
        updated_by     = current_user["user_id"],
    )
    db.add(floor)
    db.flush()

    return _resp(201, "Floor created successfully", _fmt(floor))


# ── PATCH /we-okas/projects/{project_id}/floors/{floor_id} ───────────────────

@router.patch("/{floor_id}", status_code=200)
def update_floor(
    project_id:   int,
    floor_id:     int,
    body:         FloorUpdate,
    current_user: dict    = Depends(get_current_user),
    db:           Session = Depends(get_orm_session),
):
    if not _visible_project(db, project_id, current_user):
        return _err(404, f"Project {project_id} not found")

    floor = db.query(Floor).filter(
        Floor.id == floor_id,
        Floor.project_id == project_id,
        Floor.active_ind == True,
    ).first()
    if not floor:
        return _err(404, f"Floor {floor_id} not found")

    if body.floor_name is not None:
        floor.name = body.floor_name
    if body.floor_pos is not None:
        floor.floor_number = body.floor_pos
    if body.floor_description is not None:
        floor.short_code = body.floor_description

    floor.updated_by = current_user["user_id"]
    db.flush()

    return _resp(200, "Floor updated successfully", _fmt(floor))
