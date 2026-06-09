"""
/health route — lightweight liveness probe
"""

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health check",
    description="Returns service status. Use as a liveness/readiness probe.",
)
def health_check():
    return {
        "status": "healthy",
        "service": "Stratify 2.0 — Client Lifecycle Automation API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
