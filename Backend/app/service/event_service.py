"""
services/event_service.py — Business logic for security events.

Handles all DB reads/writes for the events table,
keeping route handlers free of query logic.
"""

from datetime import datetime
from sqlalchemy.orm import Session as DBSession

from app.models import Event as EventModel
from app.schemas import EventRequest
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ── Create ────────────────────────────────────────────────────────────────────

def record_event(payload: EventRequest, db: DBSession) -> EventModel:
    """
    Persist a single security event from reporter.py.
    Parses the reporter timestamp string ("%Y-%m-%d %H:%M:%S");
    falls back to utcnow() if missing or malformed.
    """
    ts = datetime.utcnow()
    if payload.timestamp:
        try:
            ts = datetime.strptime(payload.timestamp, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            logger.warning(
                "record_event: unparseable timestamp %r — using utcnow",
                payload.timestamp,
            )

    event = EventModel(
        session_id = payload.session_id,
        event_type = payload.event_type,
        detail     = payload.detail,
        timestamp  = ts,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    logger.info(
        "record_event: id=%-5s  type=%-22s  session=%s  detail=%s",
        event.id,
        event.event_type,
        event.session_id,
        event.detail[:80],
    )
    return event


# ── Queries ───────────────────────────────────────────────────────────────────

def get_event_by_id(event_id: int, db: DBSession) -> EventModel | None:
    """Return a single event row by PK, or None."""
    return db.query(EventModel).filter(EventModel.id == event_id).first()


def get_events(
    db:         DBSession,
    session_id: str | None = None,
    event_type: str | None = None,
    skip:       int = 0,
    limit:      int = 100,
) -> tuple[int, list[EventModel]]:
    """
    Return (total_count, page_of_rows) newest-first.

    Filters
    -------
    session_id  — restrict to one session
    event_type  — e.g. "domain_blocked", "vpn_detected"
    """
    q = db.query(EventModel)

    if session_id:
        q = q.filter(EventModel.session_id == session_id)
    if event_type:
        q = q.filter(EventModel.event_type == event_type)

    total = q.count()
    rows  = (
        q.order_by(EventModel.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return total, rows


def get_events_for_session(
    session_id: str,
    db:         DBSession,
) -> list[EventModel]:
    """Return all events for a session ordered oldest → newest."""
    return (
        db.query(EventModel)
        .filter(EventModel.session_id == session_id)
        .order_by(EventModel.timestamp.asc())
        .all()
    )


def count_by_type(session_id: str, db: DBSession) -> dict[str, int]:
    """
    Return a dict of  { event_type: count }  for a given session.
    Useful for dashboard summary cards.
    """
    rows = (
        db.query(EventModel.event_type, EventModel.id)
        .filter(EventModel.session_id == session_id)
        .all()
    )
    counts: dict[str, int] = {}
    for event_type, _ in rows:
        counts[event_type] = counts.get(event_type, 0) + 1
    return counts