"""
app/models.py — SQLAlchemy ORM models for InterviewGuard.
Tables: sessions, events, users
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id              = Column(Integer, primary_key=True, index=True)
    session_id      = Column(String, unique=True, index=True, nullable=False)
    candidate_name  = Column(String, nullable=False)
    candidate_email = Column(String, nullable=True, default="")
    start_time      = Column(DateTime, default=datetime.utcnow)
    end_time        = Column(DateTime, nullable=True)
    status          = Column(String, default="active")  # "active" | "ended"

    # Relationship — one session has many events
    events = relationship("Event", back_populates="session",
                          cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"

    id             = Column(Integer, primary_key=True, index=True)
    session_id     = Column(String, ForeignKey("sessions.session_id"), nullable=False)
    event_type     = Column(String, nullable=False)   # domain_blocked, process_killed, etc.
    detail         = Column(String, nullable=True, default="")
    candidate_name = Column(String, nullable=True, default="")
    timestamp      = Column(DateTime, default=datetime.utcnow)

    # Relationship back to session
    session = relationship("Session", back_populates="events")


class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    full_name       = Column(String, nullable=False)
    email           = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    university      = Column(String, nullable=True)
    role            = Column(String, default="student")  # "student" | "admin"
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
