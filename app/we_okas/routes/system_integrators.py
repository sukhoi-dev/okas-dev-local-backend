import csv
import io
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.base import get_session
from app.models.auth import Organization, AppUser
from app.we_okas.deps import require_distributor

router = APIRouter(
    prefix="/api/distributors",
    tags=["we-okas | system-integrators"],
    redirect_slashes=False,
)


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class SICreate(BaseModel):
    name: str                         # company name → organizations.name
    contact_name: str                 # contact person → organizations.contact_name
    email: EmailStr                   # → organizations.email
    phone: Optional[str] = None       # → organizations.phone
    address: Optional[str] = None     # → organizations.address
    gst_vat_number: Optional[str] = None
    status: str = "Active"            # Active → active_ind=True, Inactive → False


class SIUpdate(BaseModel):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    gst_vat_number: Optional[str] = None
    status: Optional[str] = None


class StatusBody(BaseModel):
    status: str  # "Active" | "Inactive"


# ── SQL ──────────────────────────────────────────────────────────────────────

_DETAIL_SQL = """
    SELECT
        o.id,
        o.contact_name,
        o.name,
        o.address,
        o.email,
        o.phone,
        o.gst_vat_number,
        o.active_ind,
        o.created_at,
        o.updated_at
    FROM organizations o
"""


def _serialize(row) -> dict:
    r = dict(row)
    for field in ("created_at", "updated_at"):
        if r.get(field):
            r[field] = r[field].isoformat()
    r["status"] = "Active" if r.get("active_ind") else "Inactive"
    r.pop("active_ind", None)
    return r


def _make_slug(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"{base}-{uuid.uuid4().hex[:8]}"


# ── 1. List SIs ───────────────────────────────────────────────────────────────

@router.get("/system-integrators")
def list_sis(
    search: Optional[str] = Query(None),
    name: List[str] = Query(default=[]),
    company: List[str] = Query(default=[]),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_session),
    _auth: dict = Depends(require_distributor),
):
    distributor_id = _auth["organization_id"]
    conditions = [
        "o.org_type = 'si'",
        "o.parent_organization_id = :dist_id",

    ]
    params: dict = {"dist_id": distributor_id}

    if search:
        conditions.append(
            "(o.contact_name LIKE :search OR o.name LIKE :search"
            " OR o.email LIKE :search OR o.phone LIKE :search)"
        )
        params["search"] = f"%{search}%"

    if status:
        conditions.append("o.active_ind = :active_ind")
        params["active_ind"] = 1 if status == "Active" else 0

    if name:
        placeholders = ", ".join(f":name_{i}" for i in range(len(name)))
        conditions.append(f"o.contact_name IN ({placeholders})")
        for i, n in enumerate(name):
            params[f"name_{i}"] = n

    if company:
        placeholders = ", ".join(f":company_{i}" for i in range(len(company)))
        conditions.append(f"o.name IN ({placeholders})")
        for i, c in enumerate(company):
            params[f"company_{i}"] = c

    where = "WHERE " + " AND ".join(conditions)

    total = db.execute(
        text(f"SELECT COUNT(*) AS total FROM organizations o {where}"),
        params,
    ).fetchone().total

    params["limit"] = limit
    params["offset"] = (page - 1) * limit
    rows = db.execute(
        text(f"{_DETAIL_SQL} {where} ORDER BY o.created_at DESC LIMIT :limit OFFSET :offset"),
        params,
    ).mappings().all()

    return {"data": [_serialize(r) for r in rows], "total": total, "page": page}


# ── 2. Get SI detail ──────────────────────────────────────────────────────────

@router.get("/system-integrators/{si_id}")
def get_si(
    si_id: int = Path(...),
    db: Session = Depends(get_session),
    _auth: dict = Depends(require_distributor),
):
    distributor_id = _auth["organization_id"]
    row = db.execute(
        text(
            f"{_DETAIL_SQL}"
            " WHERE o.id = :si_id"
            " AND o.parent_organization_id = :dist_id"
            " AND o.org_type = 'si'"
            ""
        ),
        {"si_id": si_id, "dist_id": distributor_id},
    ).mappings().fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="System integrator not found")

    return {"data": _serialize(row)}


# ── 3. Add new SI ─────────────────────────────────────────────────────────────

@router.post("/system-integrators", status_code=201)
def create_si(
    body: SICreate,
    db: Session = Depends(get_session),
    _auth: dict = Depends(require_distributor),
):
    distributor_id = _auth["organization_id"]
    if body.status not in {"Active", "Inactive"}:
        raise HTTPException(status_code=422, detail="status must be Active or Inactive")

    existing = db.execute(
        text("""
            SELECT id FROM organizations
            WHERE email = :email
              AND parent_organization_id = :dist_id
              AND org_type = 'si'

        """),
        {"email": body.email, "dist_id": distributor_id},
    ).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail="An SI with this email already exists")

    # 1. Create organization entry for the SI
    org = Organization(
        org_type="si",
        parent_organization_id=distributor_id,
        name=body.name,
        slug=_make_slug(body.name),
        contact_name=body.contact_name,
        email=body.email,
        phone=body.phone,
        address=body.address,
        gst_vat_number=body.gst_vat_number,
        active_ind=(body.status == "Active"),
    )
    db.add(org)
    db.flush()

    # 2. Create app_user for the SI primary contact
    user = AppUser(
        organization_id=org.id,
        email=body.email,
        full_name=body.contact_name,
        phone=body.phone,
    )
    db.add(user)
    db.flush()

    # 3. Ensure SI role (id=2) exists, then assign it
    db.execute(
        text("""
            INSERT IGNORE INTO roles (id, name, description)
            VALUES (2, 'si', 'System Integrator admin')
        """)
    )
    db.execute(
        text("""
            INSERT IGNORE INTO app_user_roles (user_id, role_id, organization_id)
            VALUES (:user_id, 2, :org_id)
        """),
        {"user_id": user.id, "org_id": org.id},
    )

    row = db.execute(
        text(f"{_DETAIL_SQL} WHERE o.id = :id"),
        {"id": org.id},
    ).mappings().fetchone()

    return {"data": _serialize(row)}


# ── 4. Edit SI ────────────────────────────────────────────────────────────────

@router.put("/system-integrators/{si_id}")
def update_si(
    body: SIUpdate,
    si_id: int = Path(...),
    db: Session = Depends(get_session),
    _auth: dict = Depends(require_distributor),
):
    distributor_id = _auth["organization_id"]
    org = db.get(Organization, si_id)
    if not org or org.parent_organization_id != distributor_id or org.org_type != "si":
        raise HTTPException(status_code=404, detail="System integrator not found")

    primary_email = org.email  # capture before update for user lookup

    if body.name is not None:
        org.name = body.name
    if body.contact_name is not None:
        org.contact_name = body.contact_name
    if body.email is not None:
        org.email = str(body.email)
    if body.phone is not None:
        org.phone = body.phone
    if body.address is not None:
        org.address = body.address
    if body.gst_vat_number is not None:
        org.gst_vat_number = body.gst_vat_number
    if body.status is not None:
        org.active_ind = (body.status == "Active")

    # Sync only the primary contact user (matched by current org email)
    if any(f is not None for f in [body.contact_name, body.phone, body.email]):
        db.execute(
            text("""
                UPDATE app_users
                SET full_name = COALESCE(:full_name, full_name),
                    phone     = COALESCE(:phone, phone),
                    email     = COALESCE(:email, email)
                WHERE organization_id = :org_id
                  AND email = :primary_email
                  AND active_ind = 1
            """),
            {
                "full_name":     body.contact_name,
                "phone":         body.phone,
                "email":         str(body.email) if body.email else None,
                "org_id":        si_id,
                "primary_email": primary_email,
            },
        )

    db.flush()

    row = db.execute(
        text(f"{_DETAIL_SQL} WHERE o.id = :id"),
        {"id": org.id},
    ).mappings().fetchone()

    return {"data": _serialize(row)}


# ── 5. Toggle status ──────────────────────────────────────────────────────────

@router.patch("/system-integrators/{si_id}/status")
def toggle_status(
    body: StatusBody,
    si_id: int = Path(...),
    db: Session = Depends(get_session),
    _auth: dict = Depends(require_distributor),
):
    distributor_id = _auth["organization_id"]
    if body.status not in {"Active", "Inactive"}:
        raise HTTPException(status_code=422, detail="status must be Active or Inactive")

    org = db.get(Organization, si_id)
    if not org or org.parent_organization_id != distributor_id or org.org_type != "si":
        raise HTTPException(status_code=404, detail="System integrator not found")

    org.active_ind = (body.status == "Active")

    # Sync app_user active state
    db.execute(
        text("UPDATE app_users SET active_ind = :val WHERE organization_id = :org_id"),
        {"val": org.active_ind, "org_id": si_id},
    )

    db.flush()

    row = db.execute(
        text(f"{_DETAIL_SQL} WHERE o.id = :id"),
        {"id": org.id},
    ).mappings().fetchone()

    return {"data": _serialize(row)}


# ── 6. Archive SI ─────────────────────────────────────────────────────────────

@router.patch("/system-integrators/{si_id}/archive")
def archive_si(
    si_id: int = Path(...),
    db: Session = Depends(get_session),
    _auth: dict = Depends(require_distributor),
):
    distributor_id = _auth["organization_id"]
    org = db.get(Organization, si_id)
    if not org or org.parent_organization_id != distributor_id or org.org_type != "si":
        raise HTTPException(status_code=404, detail="System integrator not found")

    org.active_ind = False
    return {"message": "Archived successfully"}


# ── 7. Download SI details ────────────────────────────────────────────────────

@router.get("/system-integrators/{si_id}/download")
def download_si(
    si_id: int = Path(...),
    format: str = Query("pdf", pattern="^(pdf|csv)$"),
    db: Session = Depends(get_session),
    _auth: dict = Depends(require_distributor),
):
    distributor_id = _auth["organization_id"]
    row = db.execute(
        text(
            f"{_DETAIL_SQL}"
            " WHERE o.id = :si_id"
            " AND o.parent_organization_id = :dist_id"
            " AND o.org_type = 'si'"
            ""
        ),
        {"si_id": si_id, "dist_id": distributor_id},
    ).mappings().fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="System integrator not found")

    data = _serialize(row)

    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data.keys())
        writer.writeheader()
        writer.writerow(data)
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="si_{si_id}.csv"'},
        )

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as rl_canvas

    buffer = io.BytesIO()
    c = rl_canvas.Canvas(buffer, pagesize=A4)
    _, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 60, "System Integrator Details")

    y = height - 100
    fields = [
        ("Contact Name", data.get("contact_name")),
        ("Company",      data.get("name")),
        ("Email",        data.get("email")),
        ("Phone",        data.get("phone")),
        ("Address",      data.get("address")),
        ("GST/VAT",      data.get("gst_vat_number")),
        ("Status",       data.get("status")),
        ("Created At",   data.get("created_at")),
    ]
    for label, value in fields:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, f"{label}:")
        c.setFont("Helvetica", 11)
        c.drawString(160, y, str(value or "—"))
        y -= 22

    c.save()
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="si_{si_id}.pdf"'},
    )


# ── 8. Delete SI ──────────────────────────────────────────────────────────────

@router.delete("/system-integrators/{si_id}")
def delete_si(
    si_id: int = Path(...),
    db: Session = Depends(get_session),
    _auth: dict = Depends(require_distributor),
):
    distributor_id = _auth["organization_id"]
    org = db.get(Organization, si_id)
    if not org or org.parent_organization_id != distributor_id or org.org_type != "si":
        raise HTTPException(status_code=404, detail="System integrator not found")

    org.active_ind = False

    # Deactivate the SI's app users
    db.execute(
        text("UPDATE app_users SET active_ind = 0 WHERE organization_id = :org_id"),
        {"org_id": si_id},
    )

    return {"message": "Deleted successfully"}
