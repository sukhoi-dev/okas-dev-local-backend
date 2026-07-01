from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from typing import Optional
from sqlalchemy.orm import Session
import uuid

from app.auth import get_current_user
from app.db import get_orm_session
from app.models.location import Floor, Room
from app.design_studio.routes.floors import _visible_project

router = APIRouter(
    prefix="/api/we-okas/projects/{project_id}/floors/{floor_id}/rooms",
    tags=["design-studio | rooms"],
    redirect_slashes=False,
)

_VALID_ROOM_TYPES = {
    "living_room", "bedroom", "kitchen", "bathroom", "dining_room",
    "study", "garage", "utility", "outdoor", "other",
}


def _resp(status_code: int, message: str, body=None) -> dict:
    return {"id": str(uuid.uuid4()), "status": status_code, "message": message, "body": body}


def _err(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=_resp(status_code, message))


def _fmt(r: Room) -> dict:
    return {
        "id":             r.id,
        "floor_id":       r.floor_id,
        "room_name":      r.name,
        "room_type":      r.room_type,
        "room_image":     r.image_url,
        "area_sqft":      float(r.area_sqft) if r.area_sqft is not None else None,
        "display_order":  r.display_order,
        "created_at":     r.created_at.isoformat() if r.created_at else None,
        "updated_at":     r.updated_at.isoformat() if r.updated_at else None,
    }


def _visible_floor(db: Session, project_id: int, floor_id: int, current_user: dict) -> Optional[Floor]:
    if not _visible_project(db, project_id, current_user):
        return None
    return db.query(Floor).filter(
        Floor.id == floor_id,
        Floor.project_id == project_id,
        Floor.active_ind == True,
    ).first()


class RoomCreate(BaseModel):
    room_name: str
    room_type: Optional[str] = "other"

    @field_validator("room_name")
    @classmethod
    def name_required(cls, v):
        if not v.strip():
            raise ValueError("room_name cannot be empty")
        return v.strip()

    @field_validator("room_type")
    @classmethod
    def valid_type(cls, v):
        if v and v not in _VALID_ROOM_TYPES:
            return "other"
        return v or "other"


# ── GET /we-okas/projects/{project_id}/floors/{floor_id}/rooms ───────────────

@router.get("", status_code=200)
def list_rooms(
    project_id:   int,
    floor_id:     int,
    current_user: dict    = Depends(get_current_user),
    db:           Session = Depends(get_orm_session),
):
    if not _visible_floor(db, project_id, floor_id, current_user):
        return _err(404, f"Floor {floor_id} not found")

    rooms = (
        db.query(Room)
        .filter(Room.floor_id == floor_id, Room.active_ind == True)
        .order_by(Room.display_order, Room.id)
        .all()
    )
    return _resp(200, "Rooms fetched successfully", {"rooms": [_fmt(r) for r in rooms]})


# ── POST /we-okas/projects/{project_id}/floors/{floor_id}/rooms ──────────────

@router.post("", status_code=201)
def create_room(
    project_id:   int,
    floor_id:     int,
    body:         RoomCreate,
    current_user: dict    = Depends(get_current_user),
    db:           Session = Depends(get_orm_session),
):
    if not _visible_floor(db, project_id, floor_id, current_user):
        return _err(404, f"Floor {floor_id} not found")

    next_order = (
        db.query(Room)
        .filter(Room.floor_id == floor_id, Room.active_ind == True)
        .count()
    )

    room = Room(
        floor_id      = floor_id,
        name          = body.room_name,
        room_type     = body.room_type,
        display_order = next_order,
        active_ind    = True,
        updated_by    = current_user["user_id"],
    )
    db.add(room)
    db.flush()

    return _resp(201, "Room created successfully", _fmt(room))
