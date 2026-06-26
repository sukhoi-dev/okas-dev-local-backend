from fastapi import APIRouter
from app.db import get_db

router = APIRouter(tags=["lookup"])


@router.get("/api/app-users")
def list_app_users():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, full_name, email FROM app_users WHERE active_ind = 1 ORDER BY full_name"
            )
            rows = cur.fetchall()
    return {"success": True, "data": rows}


@router.get("/api/homeowners")
def list_homeowners():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, full_name, email, phone FROM homeowners WHERE active_ind = 1 ORDER BY full_name"
            )
            rows = cur.fetchall()
    return {"success": True, "data": rows}


@router.get("/api/organizations")
def list_organizations():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, slug FROM organizations WHERE active_ind = 1 ORDER BY name"
            )
            rows = cur.fetchall()
    return {"success": True, "data": rows}
