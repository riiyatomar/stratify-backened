"""
Stratify 2.0 — AI-Powered Client Lifecycle Automation Platform
==============================================================

Application entrypoint.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routes import health, requirements, proposals, plans, scope_check


# ──────────────────────────────────────────────
#  Lifespan — runs on startup / shutdown
# ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    init_db()
    print("[OK]  Database tables created / verified.")
    yield
    print("[STOP]  Shutting down Stratify 2.0 API.")


# ──────────────────────────────────────────────
#  Application
# ──────────────────────────────────────────────
app = FastAPI(
    title="Stratify 2.0 — Client Lifecycle Automation API",
    description=(
        "AI-powered backend for automating the client lifecycle: "
        "requirement intake, proposal generation, project planning, "
        "and scope-control auditing."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc
)

# ──────────────────────────────────────────────
#  CORS (allow Postman & any frontend)
# ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
#  Register routers
# ──────────────────────────────────────────────
app.include_router(health.router)
app.include_router(requirements.router)
app.include_router(proposals.router)
app.include_router(plans.router)
app.include_router(scope_check.router)


# ──────────────────────────────────────────────
#  Root redirect → docs
# ──────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def root():
    return {
        "message": "Welcome to Stratify 2.0 API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }
