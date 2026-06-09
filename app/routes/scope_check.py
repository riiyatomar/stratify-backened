"""
/scope-check routes
===================
POST /scope-check — Compare a new request against original scope
GET  /scope-check — List all scope-check records
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ScopeCheck
from app.schemas import ScopeCheckCreate, ScopeCheckResponse
from app.engine.scope_checker import check_scope

router = APIRouter(prefix="/scope-check", tags=["Scope Control"])


# ──────────────────────────────────────────────
#  POST /scope-check
# ──────────────────────────────────────────────
@router.post(
    "",
    response_model=ScopeCheckResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Evaluate scope change",
    description="Compares a new client request against the original agreed requirement "
                "and determines whether it constitutes extra work (scope creep).",
)
def create_scope_check(body: ScopeCheckCreate, db: Session = Depends(get_db)):
    # Run the scope-control engine
    result = check_scope(
        original_requirement=body.original_requirement,
        new_request=body.new_request,
    )

    # Persist
    record = ScopeCheck(
        original_requirement=body.original_requirement,
        new_request=body.new_request,
        is_extra_work=result.is_extra_work,
        explanation=result.explanation,
        additional_cost_estimate=result.additional_cost_estimate,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return record


# ──────────────────────────────────────────────
#  GET /scope-check
# ──────────────────────────────────────────────
@router.get(
    "",
    response_model=list[ScopeCheckResponse],
    summary="List all scope checks",
)
def list_scope_checks(db: Session = Depends(get_db)):
    return db.query(ScopeCheck).order_by(ScopeCheck.id.desc()).all()
