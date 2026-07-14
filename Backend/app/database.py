"""
app/database.py — SQLAlchemy engine, session factory, and Base.

The SQLite DB is stored at  data/interviewguard.db  relative to
the project root so it survives restarts without extra config.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# ── Resolve DB path ───────────────────────────────────────────────────────────

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB_PATH  = os.path.join(_BASE_DIR, "data", "interviewguard.db")
os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)

DATABASE_URL = f"sqlite:///{_DB_PATH}"

# ── Engine ────────────────────────────────────────────────────────────────────

engine = create_engine(
    DATABASE_URL,
    connect_args = {"check_same_thread": False},  # required for SQLite + FastAPI
    echo         = False,
)

# ── Session factory ───────────────────────────────────────────────────────────

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Declarative base ──────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── FastAPI dependency ────────────────────────────────────────────────────────

def get_db():
    """Yield a DB session; always closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()