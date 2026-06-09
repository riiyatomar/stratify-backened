"""
Proposal Generator Engine
=========================
Creates a professional proposal from a previously analyzed requirement.

Inputs:  Requirement record (with extracted features)
Outputs: project summary, feature list, cost estimate, timeline
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from app.config import HOURLY_RATE


@dataclass
class ProposalResult:
    project_summary: str
    feature_list: list[dict[str, Any]]
    cost_estimate: float
    timeline: str


def generate_proposal(
    client_description: str,
    features: list[dict],
    complexity: str,
    complexity_score: float,
    timeline_estimate: str,
) -> ProposalResult:
    """
    Build a proposal from the analyzed requirement data.

    Pricing model:
    - Base cost  = sum(feature hours) × HOURLY_RATE
    - Complexity multiplier scales with complexity_score
    - Contingency buffer of 15 %
    """

    # — Feature list enrichment ————————————————————————————
    enriched_features: list[dict[str, Any]] = []
    total_hours = 0.0

    for feat in features:
        hours = feat.get("estimated_hours", 20)
        total_hours += hours
        enriched_features.append({
            "name": feat["name"],
            "description": feat["description"],
            "estimated_hours": hours,
            "complexity": feat.get("complexity", "medium"),
            "cost": round(hours * HOURLY_RATE, 2),
        })

    # — Cost estimate ——————————————————————————————————————
    base_cost = total_hours * HOURLY_RATE

    # Complexity multiplier: 1.0 (low) → 1.6 (critical)
    multiplier = 1.0 + (complexity_score / 10) * 0.6
    adjusted_cost = base_cost * multiplier

    # 15 % contingency
    contingency = adjusted_cost * 0.15
    total_cost = round(adjusted_cost + contingency, 2)

    # — Project summary ————————————————————————————————————
    num_features = len(enriched_features)
    summary_lines = [
        f"This proposal covers the development of a {complexity}-complexity project "
        f"comprising {num_features} major feature{'s' if num_features != 1 else ''}.",
        "",
        f"Project Overview: {client_description[:200]}{'...' if len(client_description) > 200 else ''}",
        "",
        f"The estimated total effort is {total_hours:.0f} developer-hours, "
        f"with a complexity multiplier of {multiplier:.2f}x applied based on "
        f"the overall complexity score of {complexity_score}/10.",
        "",
        f"A 15% contingency buffer (${contingency:,.2f}) has been included to "
        f"accommodate scope adjustments and unforeseen technical challenges.",
        "",
        "Key deliverables include:",
    ]
    for feat in enriched_features:
        summary_lines.append(f"  • {feat['name']} — {feat['description'][:80]}")

    project_summary = "\n".join(summary_lines)

    # — Timeline refinement ————————————————————————————————
    # Add buffer to the raw timeline based on complexity
    parts = timeline_estimate.replace("weeks", "").strip().split("-")
    try:
        low_w = int(parts[0].strip())
        high_w = int(parts[1].strip())
    except (ValueError, IndexError):
        low_w, high_w = 4, 8

    buffer_weeks = math.ceil(complexity_score * 0.3)
    timeline = f"{low_w + buffer_weeks}-{high_w + buffer_weeks} weeks"

    return ProposalResult(
        project_summary=project_summary,
        feature_list=enriched_features,
        cost_estimate=total_cost,
        timeline=timeline,
    )
