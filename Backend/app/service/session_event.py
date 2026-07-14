"""
services/session_service.py — Business logic for session lifecycle.

All DB writes that used to live in the route handlers are here,
keeping routes thin and this layer independently testable.
"""

from datetime import datetime
from sqlalchemy.orm import Session as DBSession

from app.models import Session as SessionModel
from app.schemas import SessionStartRequest, SessionEndRequest
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ── Start ─────────────────────────────────────────────────────────────────────

def create_session(payload: SessionStartRequest, db: DBSession) -> SessionModel:
    """
    Insert a new session row.
    Returns the existing row silently if session_id is a duplicate
    (reporter may retry on network error).
    """
    existing = (
        db.query(SessionModel)
        .filter(SessionModel.session_id == payload.session_id)
        .first()
    )
    if existing:
        logger.warning(
            "create_session: duplicate session_id=%s — returning existing row",
            payload.session_id,
        )
        return existing

    session = SessionModel(
        session_id      = payload.session_id,
        candidate_name  = payload.candidate_name,
        candidate_email = payload.candidate_email,
        start_time      = datetime.utcnow(),
        end_time        = None,
        status          = "active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    logger.info(
        "create_session: started  id=%s  candidate=%s <%s>",
        session.session_id,
        session.candidate_name,
        session.candidate_email,
    )
    return session


# ── End ───────────────────────────────────────────────────────────────────────

def close_session(payload: SessionEndRequest, db: DBSession) -> SessionModel:
    """
    Mark a session as ended.
    If the row does not exist yet (end arrived before start due to offline
    queue reordering) a stub row is created first.
    """
    session = (
        db.query(SessionModel)
        .filter(SessionModel.session_id == payload.session_id)
        .first()
    )

    if not session:
        logger.warning(
            "close_session: session_id=%s not found — creating stub",
            payload.session_id,
        )
        session = SessionModel(
            session_id      = payload.session_id,
            candidate_name  = payload.candidate_name,
            candidate_email = payload.candidate_email,
            start_time      = datetime.utcnow(),
            end_time        = None,
            status          = "active",
        )
        db.add(session)
        db.flush()

    session.end_time = datetime.utcnow()
    session.status   = "ended"
    db.commit()
    db.refresh(session)

    logger.info(
        "close_session: ended  id=%s  duration=%ss",
        session.session_id,
        payload.duration_seconds,
    )
    return session


# ── Queries ───────────────────────────────────────────────────────────────────

def get_session_by_id(session_id: str, db: DBSession) -> SessionModel | None:
    """Return a single session by its string session_id, or None."""
    return (
        db.query(SessionModel)
        .filter(SessionModel.session_id == session_id)
        .first()
    )


def get_all_sessions(
    db:     DBSession,
    skip:   int = 0,
    limit:  int = 50,
    active: bool | None = None,
) -> tuple[int, list[SessionModel]]:
    """
    Return (total_count, page_of_rows) newest-first.
    active=True  → status == 'active'
    active=False → status == 'ended'
    active=None  → no filter
    """
    q = db.query(SessionModel)

    if active is True:
        q = q.filter(SessionModel.status == "active")
    elif active is False:
        q = q.filter(SessionModel.status == "ended")

    total = q.count()
    rows  = (
        q.order_by(SessionModel.start_time.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return total, rows