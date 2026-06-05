from dotenv import load_dotenv
load_dotenv()

import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── We.OKAS routes ────────────────────────────────────────────────────────
from app.we_okas.routes.auth import router as we_okas_auth_router
from app.we_okas.routes.members import router as we_okas_members_router
from app.we_okas.routes.projects import router as we_okas_projects_router
from app.we_okas.routes.roles import router as we_okas_roles_router

# ── Design Studio routes ──────────────────────────────────────────────────
# (add imports here as design_studio routes are built)

# ── Shared API routes ─────────────────────────────────────────────────────
from app.shared_api.routes.lookup import router as shared_lookup_router

app = FastAPI(
    title="OKAS Cloud API",
    description="Backend API for the OKAS smart-home platform.",
    version="1.0.0",
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Unified error response format ─────────────────────────────────────────

def _err_body(status_code: int, message: str, detail=None) -> dict:
    return {
        "id":      str(uuid.uuid4()),
        "status":  status_code,
        "message": message,
        "body":    detail,
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_err_body(exc.status_code, exc.detail),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=_err_body(422, "Validation error", exc.errors()),
    )


# ── Mount routers ─────────────────────────────────────────────────────────
app.include_router(we_okas_auth_router)
app.include_router(we_okas_members_router)
app.include_router(we_okas_projects_router)
app.include_router(we_okas_roles_router)
app.include_router(shared_lookup_router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "service": "okas-cloud-backend"}
