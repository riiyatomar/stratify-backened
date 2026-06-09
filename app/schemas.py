"""
Pydantic schemas for request / response validation.

Naming convention
-----------------
- *Create  → request body sent by the client
- *Response → data returned to the client
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════
#  Requirement
# ═══════════════════════════════════════════════
class RequirementCreate(BaseModel):
    """POST /requirements — body."""
    client_description: str = Field(
        ...,
        min_length=10,
        description="Free-text description of what the client needs.",
        json_schema_extra={"example": "Build an e-commerce platform with user authentication, product catalog, shopping cart, payment integration via Stripe, and an admin dashboard for inventory management."},
    )


class FeatureDetail(BaseModel):
    """Single extracted feature."""
    name: str
    description: str
    estimated_hours: float
    complexity: str  # low / medium / high


class RequirementResponse(BaseModel):
    """POST /requirements — response."""
    id: int
    client_description: str
    features: list[FeatureDetail]
    timeline_estimate: str
    complexity: str
    complexity_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════
#  Proposal
# ═══════════════════════════════════════════════
class ProposalCreate(BaseModel):
    """POST /proposal — body."""
    requirement_id: int = Field(
        ...,
        description="ID of the requirement to generate a proposal for.",
        json_schema_extra={"example": 1},
    )


class ProposalResponse(BaseModel):
    """POST /proposal — response."""
    id: int
    requirement_id: int
    project_summary: str
    feature_list: list[dict]
    cost_estimate: float
    timeline: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════
#  Plan
# ═══════════════════════════════════════════════
class PlanCreate(BaseModel):
    """POST /plan — body."""
    requirement_id: int = Field(
        ...,
        description="ID of the requirement to generate a project plan for.",
        json_schema_extra={"example": 1},
    )


class TaskItem(BaseModel):
    """Single task in the breakdown."""
    task_id: int
    name: str
    description: str
    assigned_phase: str
    estimated_hours: float
    dependencies: list[int] = []


class WeeklySchedule(BaseModel):
    """Single week in the timeline."""
    week: int
    focus: str
    tasks: list[str]
    deliverables: list[str]


class Milestone(BaseModel):
    """Project milestone."""
    name: str
    target_week: int
    criteria: str


class PlanResponse(BaseModel):
    """POST /plan — response."""
    id: int
    requirement_id: int
    task_breakdown: list[TaskItem]
    weekly_timeline: list[WeeklySchedule]
    milestones: list[Milestone]
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════
#  Scope Check
# ═══════════════════════════════════════════════
class ScopeCheckCreate(BaseModel):
    """POST /scope-check — body."""
    original_requirement: str = Field(
        ...,
        min_length=10,
        description="The original agreed-upon requirement.",
        json_schema_extra={"example": "Build an e-commerce platform with user auth, product catalog, cart, and Stripe payments."},
    )
    new_request: str = Field(
        ...,
        min_length=5,
        description="The new request from the client to evaluate.",
        json_schema_extra={"example": "Add a real-time chat support system and AI-powered product recommendations."},
    )


class ScopeCheckResponse(BaseModel):
    """POST /scope-check — response."""
    id: int
    original_requirement: str
    new_request: str
    is_extra_work: bool
    explanation: str
    additional_cost_estimate: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}
