"""
routes/session.py — Session lifecycle endpoints.

POST /session/start   → called by reporter.py when exam begins
POST /session/end     → called by reporter.py when exam ends
GET  /sessions        → list all sessions (dashboard)
GET  /sessions/{id}   → single session detail with its events
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app.models import Session as SessionModel, Event as EventModel
from app.schemas import (
    SessionStartRequest,
    SessionEndRequest,
    SessionResponse,
    SessionListResponse,
    OKResponse,
    EventResponse,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Sessions"])


# ── Helper — build SessionResponse from ORM row ───────────────────────────────

def _to_response(row: SessionModel) -> SessionResponse:
    return SessionResponse(
        id               = row.id,
        session_id       = row.session_id,
        candidate_name   = row.candidate_name,
        candidate_email  = row.candidate_email,
        role             = "",                   # not in this model
        started_at       = row.start_time,
        ended_at         = row.end_time,
        duration_seconds = None,
        is_active        = (row.status == "active"),
        event_count      = len(row.events) if row.events else 0,
    )


# ── POST /session/start ───────────────────────────────────────────────────────

@router.post("/session/start", response_model=OKResponse, status_code=201)
def start_session(payload: SessionStartRequest, db: DBSession = Depends(get_db)):
    """
    Called by reporter.py → Reporter.start_session().
    Creates a new session row. If the session_id already exists (duplicate
    start) the existing row is returned without error so the client stays happy.
    """
    existing = (
        db.query(SessionModel)
        .filter(SessionModel.session_id == payload.session_id)
        .first()
    )
    if existing:
        logger.warning("Duplicate session_start ignored: %s", payload.session_id)
        return OKResponse(message="session already exists")

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
        "Session STARTED  id=%s  candidate=%s <%s>",
        session.session_id, session.candidate_name, session.candidate_email,
    )
    return OKResponse(message=f"session {session.session_id} started")


# ── POST /session/end ─────────────────────────────────────────────────────────

@router.post("/session/end", response_model=OKResponse)
def end_session(payload: SessionEndRequest, db: DBSession = Depends(get_db)):
    """
    Called by reporter.py → Reporter.end_session().
    Marks the session ended and stamps end_time + status.
    """
    session = (
        db.query(SessionModel)
        .filter(SessionModel.session_id == payload.session_id)
        .first()
    )
    if not session:
        # reporter may fire end before start arrives — create a stub row
        logger.warning("session/end received for unknown id=%s — creating stub", payload.session_id)
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

    logger.info(
        "Session ENDED    id=%s  duration=%ss",
        session.session_id, payload.duration_seconds,
    )
    return OKResponse(message=f"session {session.session_id} ended")


# ── GET /sessions ─────────────────────────────────────────────────────────────

@router.get("/sessions", response_model=SessionListResponse)
def list_sessions(
    skip:   int = Query(0,   ge=0,  description="Offset for pagination"),
    limit:  int = Query(50,  ge=1, le=200, description="Max rows to return"),
    active: bool | None = Query(None, description="Filter by active status"),
    db: DBSession = Depends(get_db),
):
    """Return a paginated list of all sessions, newest first."""
    q = db.query(SessionModel)

    if active is True:
        q = q.filter(SessionModel.status == "active")
    elif active is False:
        q = q.filter(SessionModel.status == "ended")

    total    = q.count()
    sessions = q.order_by(SessionModel.start_time.desc()).offset(skip).limit(limit).all()

    return SessionListResponse(
        total    = total,
        sessions = [_to_response(s) for s in sessions],
    )


# ── GET /sessions/{session_id} ────────────────────────────────────────────────

@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: DBSession = Depends(get_db)):
    """Return a single session record, including its event_count."""
    session = (
        db.query(SessionModel)
        .filter(SessionModel.session_id == session_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    return _to_response(session)


# ── GET /sessions/{session_id}/events ─────────────────────────────────────────

@router.get("/sessions/{session_id}/events", response_model=list[EventResponse])
def get_session_events(session_id: str, db: DBSession = Depends(get_db)):
    """Return every event that belongs to a session, oldest first."""
    session = (
        db.query(SessionModel)
        .filter(SessionModel.session_id == session_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    events = (
        db.query(EventModel)
        .filter(EventModel.session_id == session_id)
        .order_by(EventModel.timestamp)
        .all()
    )
    return [
        EventResponse(
            id             = e.id,
            session_id     = e.session_id,
            event_type     = e.event_type,
            detail         = e.detail,
            timestamp      = e.timestamp,
            candidate_name = e.candidate_name,
        )
        for e in events
    ]