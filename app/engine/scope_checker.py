"""
Scope Control Engine
====================
Compares a new client request against the original agreed requirement
and determines whether the new request constitutes extra work.

Uses:
  • keyword overlap analysis
  • feature extraction diff
  • effort delta estimation
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from app.config import HOURLY_RATE, COMPLEXITY_WEIGHTS
from app.engine.requirement_analyzer import _FEATURE_KEYWORDS


@dataclass
class ScopeCheckResult:
    is_extra_work: bool
    explanation: str
    additional_cost_estimate: Optional[float]


# Common English stop words to exclude from overlap analysis.
# These dilute the ratio without carrying meaningful scope information.
_STOP_WORDS: set[str] = {
    "a", "an", "the", "is", "it", "in", "on", "at", "to", "of", "for",
    "and", "or", "but", "not", "with", "by", "from", "as", "be", "are",
    "was", "were", "been", "has", "have", "had", "do", "does", "did",
    "will", "would", "shall", "should", "can", "could", "may", "might",
    "must", "this", "that", "these", "those", "i", "you", "we", "he",
    "she", "they", "me", "us", "him", "her", "them", "my", "your",
    "our", "his", "its", "their", "what", "which", "who", "whom",
    "how", "when", "where", "why", "if", "so", "no", "yes", "also",
    "just", "more", "most", "very", "too", "all", "each", "every",
    "some", "any", "many", "much", "few", "other", "new", "old",
    "make", "show", "get", "set", "add", "use", "want", "need",
    "like", "please", "top", "bottom", "left", "right", "page",
    "display", "view", "section", "part", "way", "able", "sure",
    "think", "know", "see", "look", "put", "go", "take", "come",
}


def _extract_feature_keys(text: str) -> set[str]:
    """Return the set of recognised feature keys present in the text."""
    text_lower = text.lower()
    found: set[str] = set()
    for key, meta in _FEATURE_KEYWORDS.items():
        triggers = [key] + meta["aliases"]
        if any(t in text_lower for t in triggers):
            found.add(key)
    return found


def _word_set(text: str) -> set[str]:
    """Normalised word set for overlap analysis — stop words removed."""
    raw = set(re.findall(r"[a-z]+", text.lower()))
    return raw - _STOP_WORDS


def check_scope(
    original_requirement: str,
    new_request: str,
) -> ScopeCheckResult:
    """
    Determine whether *new_request* falls outside the scope of
    *original_requirement*.

    Strategy:
    1. Extract recognised feature sets from both texts.
    2. Compute the *new features* = features in new_request but NOT in original.
    3. If new features exist → extra work.  Estimate cost.
    4. If new request features are a SUBSET of original features → in scope.
    5. If no features matched at all, fall back to word-overlap heuristic
       (with stop words removed):
       – if < 40 % overlap → likely extra work.
    """

    original_features = _extract_feature_keys(original_requirement)
    new_features_all = _extract_feature_keys(new_request)

    extra_features = new_features_all - original_features

    # ── Case 1: clearly new features detected ────────────
    if extra_features:
        extra_hours = 0.0
        feature_descriptions: list[str] = []

        for key in extra_features:
            meta = _FEATURE_KEYWORDS[key]
            weight = COMPLEXITY_WEIGHTS.get(key, 1.0)
            hours = meta["base_hours"] * weight
            extra_hours += hours
            feature_descriptions.append(
                f"• {key.replace('-', ' ').title()} (~{hours:.0f} hrs): {meta['description'][:90]}"
            )

        additional_cost = round(extra_hours * HOURLY_RATE, 2)

        explanation_parts = [
            "The new request introduces functionality NOT covered by the original scope:",
            "",
            *feature_descriptions,
            "",
            f"Estimated additional effort: {extra_hours:.0f} developer-hours.",
            f"Estimated additional cost: ${additional_cost:,.2f} (at ${HOURLY_RATE}/hr).",
            "",
            "Recommendation: Create a change-request document and obtain sign-off "
            "before proceeding with the additional work.",
        ]

        return ScopeCheckResult(
            is_extra_work=True,
            explanation="\n".join(explanation_parts),
            additional_cost_estimate=additional_cost,
        )

    # ── Case 2: new request references only features already in scope ──
    # If the new request mentions recognisable features and ALL of them
    # are already covered by the original, it is clearly in-scope work.
    if new_features_all and new_features_all.issubset(original_features):
        shared = ", ".join(sorted(new_features_all)).replace("-", " ").title()
        return ScopeCheckResult(
            is_extra_work=False,
            explanation=(
                f"The new request relates to features already included in the "
                f"original scope ({shared}). No additional features were detected.\n\n"
                f"Recommendation: Proceed without a change-request, but document the "
                f"clarification for audit purposes."
            ),
            additional_cost_estimate=None,
        )

    # ── Case 3: no features matched at all — use word overlap ──
    original_words = _word_set(original_requirement)
    new_words = _word_set(new_request)

    if not new_words:
        return ScopeCheckResult(
            is_extra_work=False,
            explanation="The new request appears empty or too short to analyze.",
            additional_cost_estimate=None,
        )

    overlap = original_words & new_words
    overlap_ratio = len(overlap) / len(new_words)

    if overlap_ratio >= 0.40:
        return ScopeCheckResult(
            is_extra_work=False,
            explanation=(
                f"The new request appears to fall within the original scope. "
                f"Keyword analysis shows {overlap_ratio:.0%} meaningful-word overlap "
                f"with the agreed requirements. No additional features were detected.\n\n"
                f"Recommendation: Proceed without a change-request, but document the "
                f"clarification for audit purposes."
            ),
            additional_cost_estimate=None,
        )

    # Low overlap AND no recognised features — ambiguous
    # Estimate a small investigation cost
    investigation_hours = 8.0
    investigation_cost = round(investigation_hours * HOURLY_RATE, 2)

    return ScopeCheckResult(
        is_extra_work=True,
        explanation=(
            f"The new request has low keyword overlap ({overlap_ratio:.0%}) with the "
            f"original scope, suggesting it may involve work outside the agreed "
            f"boundaries even though no specific new feature categories were identified.\n\n"
            f"Estimated investigation effort: {investigation_hours:.0f} hours "
            f"(${investigation_cost:,.2f}) to properly assess the request.\n\n"
            f"Recommendation: Conduct a detailed scope-impact analysis before "
            f"committing resources."
        ),
        additional_cost_estimate=investigation_cost,
    )
