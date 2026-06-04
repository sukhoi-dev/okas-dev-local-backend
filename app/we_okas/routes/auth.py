import os
import uuid

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

from app.auth import create_access_token, _TTL_H
from app.db import get_db

router = APIRouter(prefix="/we-okas/auth", tags=["we-okas | auth"], redirect_slashes=False)

_JWT_TTL_SECONDS = _TTL_H * 3600


def _resp(status_code: int, message: str, body=None) -> dict:
    return {
        "id":      str(uuid.uuid4()),
        "status":  status_code,
        "message": message,
        "body":    body,
    }


class TokenRequest(BaseModel):
    email: EmailStr


@router.post("/token")
def get_token(body: TokenRequest):
    """
    Issue a JWT for an existing app_user.
    No password required — dev / testing flow.
    Use the returned access_token as:
        Authorization: Bearer <access_token>
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.id, u.email, u.full_name, u.organization_id,
                       r.name AS role_name
                FROM app_users u
                LEFT JOIN app_user_roles aur ON aur.user_id = u.id
                LEFT JOIN roles r             ON r.id = aur.role_id
                WHERE u.email = %s AND u.active_ind = 1
                LIMIT 1
                """,
                (body.email,),
            )
            user = cur.fetchone()

    if not user:
        return JSONResponse(
            status_code=404,
            content=_resp(404, "User not found or inactive", None),
        )

    token = create_access_token(user)

    return _resp(
        200,
        "Token issued successfully",
        {
            "access_token": token,
            "token_type":   "bearer",
            "expires_in":   _JWT_TTL_SECONDS,
            "user": {
                "id":           user["id"],
                "email":        user["email"],
                "full_name":    user["full_name"],
                "role":         user["role_name"],
                "organization_id": user["organization_id"],
            },
        },
    )
