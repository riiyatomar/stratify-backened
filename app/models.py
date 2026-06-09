"""
SQLAlchemy ORM models.

Tables
------
- requirements : raw client descriptions + AI-extracted structure
- proposals    : generated proposals linked to a requirement
- plans        : project plans linked to a requirement
- scope_checks : scope-control audit records
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ──────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────
def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ──────────────────────────────────────────────
# Requirement
# ──────────────────────────────────────────────
class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)
    client_description = Column(Text, nullable=False)

    # AI-extracted fields (stored as JSON for flexibility)
    features = Column(JSON, nullable=True)
    timeline_estimate = Column(String(120), nullable=True)
    complexity = Column(String(30), nullable=True)       # low / medium / high / critical
    complexity_score = Column(Float, nullable=True)

    created_at = Column(DateTime, default=_utcnow)

    # Relationships
    proposals = relationship("Proposal", back_populates="requirement", cascade="all, delete-orphan")
    plans = relationship("Plan", back_populates="requirement", cascade="all, delete-orphan")


# ──────────────────────────────────────────────
# Proposal
# ──────────────────────────────────────────────
class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"), nullable=False)

    project_summary = Column(Text, nullable=True)
    feature_list = Column(JSON, nullable=True)
    cost_estimate = Column(Float, nullable=True)
    timeline = Column(String(120), nullable=True)

    created_at = Column(DateTime, default=_utcnow)

    requirement = relationship("Requirement", back_populates="proposals")


# ──────────────────────────────────────────────
# Plan
# ──────────────────────────────────────────────
class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"), nullable=False)

    task_breakdown = Column(JSON, nullable=True)
    weekly_timeline = Column(JSON, nullable=True)
    milestones = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=_utcnow)

    requirement = relationship("Requirement", back_populates="plans")


# ──────────────────────────────────────────────
# Scope Check
# ──────────────────────────────────────────────
class ScopeCheck(Base):
    __tablename__ = "scope_checks"

    id = Column(Integer, primary_key=True, index=True)

    original_requirement = Column(Text, nullable=False)
    new_request = Column(Text, nullable=False)

    is_extra_work = Column(Boolean, nullable=False)
    explanation = Column(Text, nullable=True)
    additional_cost_estimate = Column(Float, nullable=True)

    created_at = Column(DateTime, default=_utcnow)
