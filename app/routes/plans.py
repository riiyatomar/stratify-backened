"""
/plan routes
============
POST /plan  — Generate a project plan for a given requirement
GET  /plan  — List all plans
"""

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Requirement, Plan
from app.schemas import PlanCreate, PlanResponse
from app.engine.project_planner import generate_plan

router = APIRouter(prefix="/plan", tags=["Project Plans"])


# ──────────────────────────────────────────────
#  POST /plan
# ──────────────────────────────────────────────
@router.post(
    "",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a project plan",
    description="Accepts a requirement ID and generates a detailed project plan "
                "with task breakdown, weekly schedule, and milestones.",
)
def create_plan(body: PlanCreate, db: Session = Depends(get_db)):
    requirement = (
        db.query(Requirement)
        .filter(Requirement.id == body.requirement_id)
        .first()
    )
    if not requirement:
        raise HTTPException(
            status_code=404,
            detail=f"Requirement {body.requirement_id} not found. "
                   f"Create one first via POST /requirements.",
        )

    # Run the planner engine
    result = generate_plan(
        features=requirement.features or [],
        complexity=requirement.complexity or "medium",
        timeline_estimate=requirement.timeline_estimate or "4-6 weeks",
    )

    # Convert dataclasses to dicts for JSON storage
    task_data = [asdict(t) for t in result.task_breakdown]
    weekly_data = [asdict(w) for w in result.weekly_timeline]
    milestone_data = [asdict(m) for m in result.milestones]

    # Persist
    plan = Plan(
        requirement_id=requirement.id,
        task_breakdown=task_data,
        weekly_timeline=weekly_data,
        milestones=milestone_data,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    return plan


# ──────────────────────────────────────────────
#  GET /plan
# ──────────────────────────────────────────────
@router.get(
    "",
    response_model=list[PlanResponse],
    summary="List all project plans",
)
def list_plans(db: Session = Depends(get_db)):
    return db.query(Plan).order_by(Plan.id.desc()).all()
