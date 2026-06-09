"""
Requirement Analyzer Engine
===========================
Parses a free-text client description and extracts:
  • features (name, description, estimated hours, complexity)
  • overall complexity rating + numeric score
  • timeline estimate

This is a *deterministic, rule-based* engine — no external LLM calls.
It uses keyword matching, sentence segmentation, and heuristic scoring
so the backend is fully self-contained and runnable offline.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from app.config import COMPLEXITY_WEIGHTS, WEEKLY_HOURS


# ──────────────────────────────────────────────
#  Data classes
# ──────────────────────────────────────────────
@dataclass
class ExtractedFeature:
    name: str
    description: str
    estimated_hours: float
    complexity: str   # low | medium | high


@dataclass
class AnalysisResult:
    features: list[ExtractedFeature]
    complexity: str            # low | medium | high | critical
    complexity_score: float    # 0-10
    timeline_estimate: str     # e.g. "6-8 weeks"


# ──────────────────────────────────────────────
#  Feature keyword catalogue
# ──────────────────────────────────────────────
_FEATURE_KEYWORDS: dict[str, dict] = {
    "authentication": {
        "aliases": ["auth", "login", "signup", "sign-up", "sign up", "registration", "oauth", "sso", "jwt"],
        "base_hours": 24,
        "description": "User authentication system including registration, login, password recovery, and session management.",
    },
    "payment": {
        "aliases": ["stripe", "paypal", "billing", "checkout", "subscription", "payment gateway", "transaction"],
        "base_hours": 40,
        "description": "Payment processing integration with secure checkout, invoice generation, and transaction history.",
    },
    "real-time": {
        "aliases": ["websocket", "live", "real time", "realtime", "socket", "push notification"],
        "base_hours": 32,
        "description": "Real-time data streaming via WebSockets for live updates and notifications.",
    },
    "machine learning": {
        "aliases": ["ml", "ai model", "prediction", "recommendation engine", "neural network", "training"],
        "base_hours": 60,
        "description": "Machine learning pipeline including data preprocessing, model training, and inference API.",
    },
    "ai": {
        "aliases": ["artificial intelligence", "chatbot", "nlp", "natural language", "ai-powered", "ai powered", "gpt", "llm"],
        "base_hours": 48,
        "description": "AI-powered features such as intelligent automation, NLP processing, or conversational interfaces.",
    },
    "integration": {
        "aliases": ["third-party", "third party", "api integration", "external api", "webhook", "connect"],
        "base_hours": 20,
        "description": "Third-party service integration including API connectors, webhooks, and data synchronization.",
    },
    "notification": {
        "aliases": ["email", "sms", "alert", "push", "in-app notification"],
        "base_hours": 16,
        "description": "Multi-channel notification system supporting email, SMS, push, and in-app alerts.",
    },
    "dashboard": {
        "aliases": ["admin panel", "admin dashboard", "control panel", "management console", "back office"],
        "base_hours": 28,
        "description": "Interactive dashboard with data visualization, KPI widgets, and management controls.",
    },
    "analytics": {
        "aliases": ["reporting", "metrics", "statistics", "data analysis", "insights", "charts", "graphs"],
        "base_hours": 30,
        "description": "Analytics and reporting module with charts, export capabilities, and data filtering.",
    },
    "file upload": {
        "aliases": ["file management", "upload", "media", "storage", "image upload", "document upload", "s3"],
        "base_hours": 18,
        "description": "File upload and management system with storage, preview, and access control.",
    },
    "search": {
        "aliases": ["full-text search", "elasticsearch", "filter", "autocomplete", "search engine"],
        "base_hours": 22,
        "description": "Advanced search functionality with filtering, autocomplete, and relevance ranking.",
    },
    "chat": {
        "aliases": ["messaging", "inbox", "conversation", "direct message", "chat system", "chat support"],
        "base_hours": 36,
        "description": "Real-time chat/messaging system with conversation history and typing indicators.",
    },
    "e-commerce": {
        "aliases": ["shop", "store", "product catalog", "shopping cart", "cart", "inventory", "order management", "product management"],
        "base_hours": 50,
        "description": "E-commerce platform with product catalog, shopping cart, order management, and inventory tracking.",
    },
    "api": {
        "aliases": ["rest api", "graphql", "api endpoints", "api gateway", "backend api"],
        "base_hours": 20,
        "description": "RESTful API layer with versioning, documentation, rate limiting, and error handling.",
    },
    "database": {
        "aliases": ["data model", "schema design", "migrations", "orm", "data layer", "database design"],
        "base_hours": 16,
        "description": "Database architecture including schema design, migrations, and query optimization.",
    },
    "security": {
        "aliases": ["encryption", "rbac", "role-based", "permission", "access control", "firewall", "audit log"],
        "base_hours": 28,
        "description": "Security hardening with encryption, RBAC, audit logging, and vulnerability protection.",
    },
    "testing": {
        "aliases": ["unit test", "integration test", "e2e", "end-to-end", "test suite", "ci/cd", "ci cd"],
        "base_hours": 20,
        "description": "Comprehensive test suite with unit, integration, and end-to-end testing plus CI/CD pipeline.",
    },
    "deployment": {
        "aliases": ["docker", "kubernetes", "k8s", "aws", "cloud deploy", "devops", "infrastructure"],
        "base_hours": 24,
        "description": "Deployment infrastructure including containerization, orchestration, and cloud provisioning.",
    },
    "monitoring": {
        "aliases": ["logging", "observability", "health check", "uptime", "apm", "error tracking"],
        "base_hours": 18,
        "description": "Application monitoring with logging, health checks, alerting, and performance tracking.",
    },
    "mobile": {
        "aliases": ["ios", "android", "react native", "flutter", "mobile app", "responsive design"],
        "base_hours": 44,
        "description": "Mobile application development or responsive mobile-first design implementation.",
    },
    "responsive": {
        "aliases": ["responsive design", "mobile-friendly", "adaptive layout"],
        "base_hours": 12,
        "description": "Responsive/adaptive UI ensuring consistent experience across screen sizes.",
    },
    "seo": {
        "aliases": ["search engine optimization", "meta tags", "schema markup", "sitemap"],
        "base_hours": 10,
        "description": "SEO optimization including meta tags, structured data, sitemap, and performance tuning.",
    },
}


# ──────────────────────────────────────────────
#  Analyzer
# ──────────────────────────────────────────────
def analyze_requirement(description: str) -> AnalysisResult:
    """
    Run the deterministic analyzer over a raw client description.

    Steps:
    1. Tokenize and normalize the input.
    2. Match against the feature catalogue → extract features.
    3. Compute per-feature complexity & hours.
    4. Aggregate into an overall complexity score + timeline.
    """
    text_lower = description.lower()

    # — Step 1: extract matching features ——————————————————
    matched_features: list[ExtractedFeature] = []
    matched_keys: set[str] = set()

    for key, meta in _FEATURE_KEYWORDS.items():
        # Check canonical name and all aliases
        triggers = [key] + meta["aliases"]
        if any(trigger in text_lower for trigger in triggers):
            if key not in matched_keys:
                matched_keys.add(key)

                weight = COMPLEXITY_WEIGHTS.get(key, 1.0)
                hours = round(meta["base_hours"] * weight, 1)

                # Per-feature complexity bucket
                if hours <= 16:
                    feat_complexity = "low"
                elif hours <= 32:
                    feat_complexity = "medium"
                else:
                    feat_complexity = "high"

                matched_features.append(
                    ExtractedFeature(
                        name=key.replace("-", " ").title(),
                        description=meta["description"],
                        estimated_hours=hours,
                        complexity=feat_complexity,
                    )
                )

    # If no known features detected, create a generic one from the description
    if not matched_features:
        matched_features.append(
            ExtractedFeature(
                name="Custom Development",
                description=f"Custom feature: {description[:120]}",
                estimated_hours=40.0,
                complexity="medium",
            )
        )

    # — Step 2: compute overall score ——————————————————————
    total_hours = sum(f.estimated_hours for f in matched_features)
    num_features = len(matched_features)

    # Score formula: blend of total effort + breadth of features
    raw_score = (total_hours / 40) + (num_features * 0.5)
    complexity_score = round(min(raw_score, 10.0), 1)

    if complexity_score <= 2.5:
        complexity = "low"
    elif complexity_score <= 5.0:
        complexity = "medium"
    elif complexity_score <= 7.5:
        complexity = "high"
    else:
        complexity = "critical"

    # — Step 3: timeline estimate ——————————————————————————
    weeks_raw = total_hours / WEEKLY_HOURS
    weeks_low = max(1, math.floor(weeks_raw))
    weeks_high = max(weeks_low + 1, math.ceil(weeks_raw * 1.3))
    timeline_estimate = f"{weeks_low}-{weeks_high} weeks"

    return AnalysisResult(
        features=matched_features,
        complexity=complexity,
        complexity_score=complexity_score,
        timeline_estimate=timeline_estimate,
    )
