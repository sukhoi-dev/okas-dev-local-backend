from fastapi import Header, HTTPException
from app.auth import _decode


def require_distributor(
    authorization: str = Header(...),
) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    try:
        payload = _decode(authorization[7:])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if payload.get("org_type") != "distributor":
        raise HTTPException(status_code=403, detail="Distributor role required")

    return {"user_id": payload["user_id"], "organization_id": payload["organization_id"]}
