from dotenv import load_dotenv
load_dotenv()  # local dev only — ignored when env vars are injected by ECS

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.projects import router as projects_router
from app.routes.users import router as users_router

app = FastAPI(
    title="OKAS Cloud API",
    description="Backend API for the OKAS smart-home platform (We.OKAS portal).",
    version="1.0.0",
    redirect_slashes=False,  # accept /api/projects and /api/projects/ equally
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router)
app.include_router(users_router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "service": "okas-cloud-backend"}
