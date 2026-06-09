"""
Project Planner Engine
======================
Generates a structured project plan from analyzed requirements:
  • task breakdown with dependencies
  • weekly timeline / sprint schedule
  • milestones with acceptance criteria
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from app.config import WEEKLY_HOURS


@dataclass
class TaskItem:
    task_id: int
    name: str
    description: str
    assigned_phase: str
    estimated_hours: float
    dependencies: list[int] = field(default_factory=list)


@dataclass
class WeeklySchedule:
    week: int
    focus: str
    tasks: list[str]
    deliverables: list[str]


@dataclass
class MilestoneItem:
    name: str
    target_week: int
    criteria: str


@dataclass
class PlanResult:
    task_breakdown: list[TaskItem]
    weekly_timeline: list[WeeklySchedule]
    milestones: list[MilestoneItem]


# ──────────────────────────────────────────────
#  Phase definitions
# ──────────────────────────────────────────────
_PHASES = [
    ("Discovery & Setup", 0.10),
    ("Core Development", 0.45),
    ("Integration & Features", 0.25),
    ("Testing & QA", 0.12),
    ("Deployment & Handoff", 0.08),
]


def generate_plan(
    features: list[dict[str, Any]],
    complexity: str,
    timeline_estimate: str,
) -> PlanResult:
    """
    Create a project plan from the analyzed feature set.
    """

    total_hours = sum(f.get("estimated_hours", 20) for f in features)

    # Parse timeline estimate (e.g. "4-6 weeks")
    parts = timeline_estimate.replace("weeks", "").strip().split("-")
    try:
        total_weeks = int(parts[1].strip())
    except (ValueError, IndexError):
        total_weeks = max(4, math.ceil(total_hours / WEEKLY_HOURS))

    # ── Task breakdown ──────────────────────────────────
    tasks: list[TaskItem] = []
    task_id = 1

    # Phase 0: project kickoff (always present)
    tasks.append(TaskItem(
        task_id=task_id,
        name="Project Kickoff & Environment Setup",
        description="Initialize repository, configure CI/CD, set up development environment, and finalize technical architecture.",
        assigned_phase="Discovery & Setup",
        estimated_hours=round(total_hours * 0.05, 1),
        dependencies=[],
    ))
    kickoff_id = task_id
    task_id += 1

    tasks.append(TaskItem(
        task_id=task_id,
        name="Requirements Finalization & Wireframes",
        description="Review requirements with stakeholders, create wireframes, and sign off on technical specifications.",
        assigned_phase="Discovery & Setup",
        estimated_hours=round(total_hours * 0.05, 1),
        dependencies=[kickoff_id],
    ))
    wireframes_id = task_id
    task_id += 1

    # Per-feature tasks
    feature_task_ids: list[int] = []
    for feat in features:
        hours = feat.get("estimated_hours", 20)
        tasks.append(TaskItem(
            task_id=task_id,
            name=f"Implement {feat['name']}",
            description=f"Develop and unit-test: {feat.get('description', feat['name'])}",
            assigned_phase="Core Development",
            estimated_hours=round(hours * 0.7, 1),
            dependencies=[wireframes_id],
        ))
        dev_id = task_id
        feature_task_ids.append(dev_id)
        task_id += 1

        tasks.append(TaskItem(
            task_id=task_id,
            name=f"Integrate {feat['name']}",
            description=f"Wire {feat['name']} into the application, write integration tests, and perform code review.",
            assigned_phase="Integration & Features",
            estimated_hours=round(hours * 0.2, 1),
            dependencies=[dev_id],
        ))
        task_id += 1

    # QA phase
    tasks.append(TaskItem(
        task_id=task_id,
        name="End-to-End Testing & QA",
        description="Execute comprehensive test plan including regression, performance, and security testing.",
        assigned_phase="Testing & QA",
        estimated_hours=round(total_hours * 0.12, 1),
        dependencies=feature_task_ids,
    ))
    qa_id = task_id
    task_id += 1

    tasks.append(TaskItem(
        task_id=task_id,
        name="Bug Fixing & Polish",
        description="Address QA findings, optimize performance, and finalize UI/UX polish.",
        assigned_phase="Testing & QA",
        estimated_hours=round(total_hours * 0.05, 1),
        dependencies=[qa_id],
    ))
    bugfix_id = task_id
    task_id += 1

    # Deployment
    tasks.append(TaskItem(
        task_id=task_id,
        name="Production Deployment",
        description="Deploy to production environment, run smoke tests, and enable monitoring.",
        assigned_phase="Deployment & Handoff",
        estimated_hours=round(total_hours * 0.04, 1),
        dependencies=[bugfix_id],
    ))
    deploy_id = task_id
    task_id += 1

    tasks.append(TaskItem(
        task_id=task_id,
        name="Documentation & Handoff",
        description="Deliver technical documentation, API docs, runbooks, and conduct knowledge-transfer sessions.",
        assigned_phase="Deployment & Handoff",
        estimated_hours=round(total_hours * 0.04, 1),
        dependencies=[deploy_id],
    ))

    # ── Weekly timeline ─────────────────────────────────
    weekly: list[WeeklySchedule] = []
    phase_weeks = []
    for phase_name, pct in _PHASES:
        w = max(1, round(total_weeks * pct))
        phase_weeks.append((phase_name, w))

    current_week = 1
    for phase_name, num_weeks in phase_weeks:
        phase_tasks = [t for t in tasks if t.assigned_phase == phase_name]
        task_names = [t.name for t in phase_tasks]

        for w in range(num_weeks):
            # Distribute tasks evenly across weeks in the phase
            start_idx = (w * len(task_names)) // num_weeks
            end_idx = ((w + 1) * len(task_names)) // num_weeks
            week_tasks = task_names[start_idx:end_idx] if task_names else [f"{phase_name} activities"]

            deliverables = []
            if w == num_weeks - 1:
                deliverables.append(f"{phase_name} phase completed")

            weekly.append(WeeklySchedule(
                week=current_week,
                focus=phase_name,
                tasks=week_tasks if week_tasks else [f"{phase_name} activities"],
                deliverables=deliverables if deliverables else [f"{phase_name} in progress"],
            ))
            current_week += 1

    # ── Milestones ──────────────────────────────────────
    milestones: list[MilestoneItem] = []
    running_week = 0
    for phase_name, num_weeks in phase_weeks:
        running_week += num_weeks
        if phase_name == "Discovery & Setup":
            milestones.append(MilestoneItem(
                name="Project Inception Complete",
                target_week=running_week,
                criteria="Environment set up, requirements signed off, architecture finalized.",
            ))
        elif phase_name == "Core Development":
            milestones.append(MilestoneItem(
                name="Core Features MVP",
                target_week=running_week,
                criteria="All core features implemented and passing unit tests.",
            ))
        elif phase_name == "Integration & Features":
            milestones.append(MilestoneItem(
                name="Integration Complete",
                target_week=running_week,
                criteria="All features integrated, integration tests passing, code reviewed.",
            ))
        elif phase_name == "Testing & QA":
            milestones.append(MilestoneItem(
                name="QA Sign-Off",
                target_week=running_week,
                criteria="All critical/high bugs resolved, test coverage > 80%, performance benchmarks met.",
            ))
        elif phase_name == "Deployment & Handoff":
            milestones.append(MilestoneItem(
                name="Production Launch",
                target_week=running_week,
                criteria="Application live in production, monitoring active, documentation delivered.",
            ))

    return PlanResult(
        task_breakdown=tasks,
        weekly_timeline=weekly,
        milestones=milestones,
    )
