"""
Database engine, session factory, and Base declarative class.
Uses SQLite via SQLAlchemy (sync driver).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

# ---------- Engine ----------
# check_same_thread=False is required for SQLite when used with FastAPI
# (multiple threads may access the same connection).
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

# ---------- Session ----------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------- Base ----------
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session
    and ensures it is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables defined on Base.metadata (idempotent)."""
    Base.metadata.create_all(bind=engine)
