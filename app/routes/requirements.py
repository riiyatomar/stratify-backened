"""
/requirements routes
====================
POST /requirements  — Analyze a client description → structured features, complexity, timeline
GET  /requirements  — List all stored requirements
GET  /requirements/{id} — Get a single requirement by ID
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Requirement
from app.schemas import RequirementCreate, RequirementResponse
from app.engine.requirement_analyzer import analyze_requirement

router = APIRouter(prefix="/requirements", tags=["Requirements"])


# ──────────────────────────────────────────────
#  POST /requirements
# ──────────────────────────────────────────────
@router.post(
    "",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze a client requirement",
    description="Accepts a free-text client description and returns extracted features, "
                "complexity score, and timeline estimate.",
)
def create_requirement(body: RequirementCreate, db: Session = Depends(get_db)):
    # Run the AI engine
    analysis = analyze_requirement(body.client_description)

    # Serialize features to dicts for JSON storage
    features_data = [
        {
            "name": f.name,
            "description": f.description,
            "estimated_hours": f.estimated_hours,
            "complexity": f.complexity,
        }
        for f in analysis.features
    ]

    # Persist
    requirement = Requirement(
        client_description=body.client_description,
        features=features_data,
        timeline_estimate=analysis.timeline_estimate,
        complexity=analysis.complexity,
        complexity_score=analysis.complexity_score,
    )
    db.add(requirement)
    db.commit()
    db.refresh(requirement)

    return requirement


# ──────────────────────────────────────────────
#  GET /requirements
# ──────────────────────────────────────────────
@router.get(
    "",
    response_model=list[RequirementResponse],
    summary="List all requirements",
)
def list_requirements(db: Session = Depends(get_db)):
    return db.query(Requirement).order_by(Requirement.id.desc()).all()


# ──────────────────────────────────────────────
#  GET /requirements/{id}
# ──────────────────────────────────────────────
@router.get(
    "/{requirement_id}",
    response_model=RequirementResponse,
    summary="Get a single requirement",
)
def get_requirement(requirement_id: int, db: Session = Depends(get_db)):
    req = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not req:
        raise HTTPException(status_code=404, detail=f"Requirement {requirement_id} not found.")
    return req
