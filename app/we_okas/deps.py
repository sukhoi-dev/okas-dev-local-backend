from fastapi import Header, HTTPException, Path
from app.auth import _decode


def require_distributor(
    distributor_id: int = Path(...),
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

    if payload.get("organization_id") != distributor_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return {"user_id": payload["user_id"], "organization_id": payload["organization_id"]}
