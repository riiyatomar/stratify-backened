"""
/proposal routes
================
POST /proposal  — Generate a proposal for a given requirement
GET  /proposal   — List all proposals
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Requirement, Proposal
from app.schemas import ProposalCreate, ProposalResponse
from app.engine.proposal_generator import generate_proposal

router = APIRouter(prefix="/proposal", tags=["Proposals"])


# ──────────────────────────────────────────────
#  POST /proposal
# ──────────────────────────────────────────────
@router.post(
    "",
    response_model=ProposalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a proposal",
    description="Accepts a requirement ID and generates a professional proposal "
                "with cost estimate, timeline, and feature breakdown.",
)
def create_proposal(body: ProposalCreate, db: Session = Depends(get_db)):
    # Fetch the requirement
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

    # Run the proposal engine
    result = generate_proposal(
        client_description=requirement.client_description,
        features=requirement.features or [],
        complexity=requirement.complexity or "medium",
        complexity_score=requirement.complexity_score or 5.0,
        timeline_estimate=requirement.timeline_estimate or "4-6 weeks",
    )

    # Persist
    proposal = Proposal(
        requirement_id=requirement.id,
        project_summary=result.project_summary,
        feature_list=result.feature_list,
        cost_estimate=result.cost_estimate,
        timeline=result.timeline,
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)

    return proposal


# ──────────────────────────────────────────────
#  GET /proposal
# ──────────────────────────────────────────────
@router.get(
    "",
    response_model=list[ProposalResponse],
    summary="List all proposals",
)
def list_proposals(db: Session = Depends(get_db)):
    return db.query(Proposal).order_by(Proposal.id.desc()).all()
