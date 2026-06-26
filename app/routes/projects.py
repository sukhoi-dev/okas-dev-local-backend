from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.db import get_db

router = APIRouter(prefix="/api/projects", tags=["projects"], redirect_slashes=False)


# ── Request / Response models ─────────────────────────────────

class PrimaryContact(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None


class ProjectCreate(BaseModel):
    name: str
    organization_id: int
    serial_number: Optional[str] = None
    project_type: Optional[str] = "residential"
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    notes: Optional[str] = None
    project_manager_id: Optional[int] = None
    primary_contact: Optional[PrimaryContact] = None


# ── GET /api/projects ─────────────────────────────────────────

@router.get("")
def list_projects():
    sql = """
        SELECT
            p.id,
            p.name,
            p.serial_number,
            p.project_type,
            p.address,
            p.city,
            p.state,
            p.installed_at,
            p.status,
            h.full_name   AS owner_name,
            h.email       AS owner_email,
            h.phone       AS owner_phone,
            u.full_name   AS manager_name,
            ps.status     AS subscription_status
        FROM projects p
        LEFT JOIN project_owners po
               ON po.project_id = p.id AND po.is_primary = 1 AND po.active_ind = 1
        LEFT JOIN homeowners h  ON h.id  = po.homeowner_id
        LEFT JOIN app_users  u  ON u.id  = p.project_manager_id
        LEFT JOIN project_subscriptions ps ON ps.project_id = p.id
        WHERE p.active_ind = 1
        ORDER BY p.created_at DESC
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    # Convert datetime to ISO string for JSON serialisation
    for r in rows:
        if r.get("installed_at"):
            r["installed_at"] = r["installed_at"].isoformat()
    return {"success": True, "data": rows}


# ── POST /api/projects ────────────────────────────────────────

@router.post("", status_code=201)
def create_project(body: ProjectCreate):
    with get_db() as conn:
        with conn.cursor() as cur:
            # 1. Insert project
            cur.execute(
                """
                INSERT INTO projects
                    (organization_id, project_manager_id, name, serial_number, project_type,
                     address, city, state, pincode, notes, installed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(3))
                """,
                (
                    body.organization_id,
                    body.project_manager_id,
                    body.name,
                    body.serial_number,
                    body.project_type,
                    body.address,
                    body.city,
                    body.state,
                    body.pincode,
                    body.notes,
                ),
            )
            project_id = cur.lastrowid

            # 2. Create / link homeowner as primary contact
            if body.primary_contact:
                cur.execute(
                    "SELECT id FROM homeowners WHERE email = %s",
                    (body.primary_contact.email,),
                )
                existing = cur.fetchone()
                if existing:
                    homeowner_id = existing["id"]
                else:
                    cur.execute(
                        "INSERT INTO homeowners (full_name, email, phone) VALUES (%s, %s, %s)",
                        (body.primary_contact.full_name, body.primary_contact.email, body.primary_contact.phone),
                    )
                    homeowner_id = cur.lastrowid

                cur.execute(
                    "INSERT INTO project_owners (project_id, homeowner_id, is_primary) VALUES (%s, %s, 1)",
                    (project_id, homeowner_id),
                )

            # 3. Re-fetch with joins
            cur.execute(
                """
                SELECT p.id, p.name, p.serial_number, p.project_type, p.address, p.city,
                       p.installed_at, p.status,
                       h.full_name AS owner_name, h.email AS owner_email, h.phone AS owner_phone,
                       u.full_name AS manager_name
                FROM projects p
                LEFT JOIN project_owners po ON po.project_id = p.id AND po.is_primary = 1
                LEFT JOIN homeowners h      ON h.id = po.homeowner_id
                LEFT JOIN app_users  u      ON u.id = p.project_manager_id
                WHERE p.id = %s
                """,
                (project_id,),
            )
            created = cur.fetchone()

    if created and created.get("installed_at"):
        created["installed_at"] = created["installed_at"].isoformat()

    return {"success": True, "data": created}
