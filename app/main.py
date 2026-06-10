from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── We.OKAS routes ────────────────────────────────────────────────────────
from app.we_okas.routes.projects import router as we_okas_projects_router
from app.we_okas.routes.system_integrators import router as we_okas_si_router

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

# ── Mount routers ─────────────────────────────────────────────────────────
app.include_router(we_okas_projects_router)
app.include_router(we_okas_si_router)
app.include_router(shared_lookup_router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "service": "okas-cloud-backend"}
