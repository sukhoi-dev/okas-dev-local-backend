import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
_ALGO   = "HS256"
_TTL_H  = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

_bearer = HTTPBearer(auto_error=False)


def create_access_token(user: dict) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub":             user["email"],
        "user_id":         user["id"],
        "full_name":       user.get("full_name") or "",
        "organization_id": user["organization_id"],
        "iat":             now,
        "exp":             now + timedelta(hours=_TTL_H),
    }
    return jwt.encode(payload, _SECRET, algorithm=_ALGO)


def _decode(token: str) -> dict:
    return jwt.decode(token, _SECRET, algorithms=[_ALGO])


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header is required")
    try:
        return _decode(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")


def require_permission(feature: str, action: str):
    """
    Dependency factory — validates JWT and checks that the user's role
    has is_allowed = TRUE for the given feature/action combination.
    """
    def _checker(current_user: dict = Depends(get_current_user)) -> dict:
        from app.db import get_db
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT rp.is_allowed
                    FROM app_user_roles aur
                    JOIN role_permissions rp ON rp.role_id = aur.role_id
                    WHERE aur.user_id = %s
                      AND rp.feature  = %s
                      AND rp.action   = %s
                    LIMIT 1
                    """,
                    (current_user["user_id"], feature, action),
                )
                row = cur.fetchone()
        if not row or not row["is_allowed"]:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {feature}.{action} access is required",
            )
        return current_user
    return _checker
