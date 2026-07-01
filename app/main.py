from dotenv import load_dotenv
load_dotenv()

import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Auth routes ───────────────────────────────────────────────────────────
from app.auth.routes.otp import router as auth_otp_router
from app.auth.routes.google import router as auth_google_router
from app.auth.routes.session import router as auth_session_router

# ── We.OKAS routes ────────────────────────────────────────────────────────
from app.we_okas.routes.auth import router as we_okas_auth_router
from app.we_okas.routes.members import router as we_okas_members_router
from app.we_okas.routes.organizations import router as we_okas_orgs_router
from app.we_okas.routes.projects import router as we_okas_projects_router
from app.we_okas.routes.roles import router as we_okas_roles_router
from app.we_okas.routes.system_integrators import router as we_okas_si_router

# ── Design Studio routes ──────────────────────────────────────────────────
from app.design_studio.routes.floors import router as design_studio_floors_router
from app.design_studio.routes.rooms import router as design_studio_rooms_router

# ── Shared API routes ─────────────────────────────────────────────────────
from app.shared_api.routes.lookup import router as shared_lookup_router

# ── Legacy / flat routes (ci/ecs-auto-deploy) ─────────────────────────────
from app.routes.projects import router as routes_projects_router
from app.routes.users import router as routes_users_router
from app.routes.admin import router as routes_admin_router
from app.routes.auth import router as routes_auth_router

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
    errors = [
        {k: (str(v) if k == "ctx" else v) for k, v in err.items()}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=_err_body(422, "Validation error", errors),
    )


# ── Mount routers ─────────────────────────────────────────────────────────
app.include_router(auth_otp_router)
app.include_router(auth_google_router)
app.include_router(auth_session_router)
app.include_router(we_okas_auth_router)
app.include_router(we_okas_members_router)
app.include_router(we_okas_orgs_router)
app.include_router(we_okas_projects_router)
app.include_router(we_okas_roles_router)
app.include_router(we_okas_si_router)
app.include_router(design_studio_floors_router)
app.include_router(design_studio_rooms_router)
app.include_router(shared_lookup_router)
app.include_router(routes_projects_router)
app.include_router(routes_users_router)
app.include_router(routes_admin_router)
app.include_router(routes_auth_router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "service": "okas-cloud-backend"}
