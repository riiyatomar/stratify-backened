"""
Application configuration.
Centralizes all config values so they can be overridden via environment variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------- Database ----------
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./stratify.db")

# ---------- AI Engine ----------
# Cost multipliers used by the proposal and scope-control engines
HOURLY_RATE: float = float(os.getenv("HOURLY_RATE", "150"))          # USD per dev-hour
WEEKLY_HOURS: int = int(os.getenv("WEEKLY_HOURS", "40"))             # hours per sprint-week

# ---------- Complexity weights (used by the requirement analyzer) ----------
COMPLEXITY_WEIGHTS: dict[str, float] = {
    "authentication": 1.5,
    "payment": 2.0,
    "real-time": 1.8,
    "machine learning": 2.5,
    "ai": 2.5,
    "integration": 1.4,
    "notification": 1.0,
    "dashboard": 1.2,
    "analytics": 1.6,
    "file upload": 1.1,
    "search": 1.3,
    "chat": 1.7,
    "e-commerce": 1.8,
    "api": 1.0,
    "database": 1.2,
    "admin panel": 1.3,
    "reporting": 1.4,
    "mobile": 1.6,
    "responsive": 0.8,
    "seo": 0.7,
    "security": 1.5,
    "testing": 0.9,
    "deployment": 1.0,
    "monitoring": 1.2,
}
