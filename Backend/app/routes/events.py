"""
routes/events.py — Security event endpoints.

POST /event              → called by reporter.py for every security event
GET  /events             → list all events (dashboard, filterable)
GET  /events/{id}        → single event detail
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app.models import Event as EventModel
from app.schemas import EventRequest, EventResponse, EventListResponse, OKResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Events"])


# ── POST /event ───────────────────────────────────────────────────────────────

@router.post("/event", response_model=OKResponse, status_code=201)
def create_event(payload: EventRequest, db: DBSession = Depends(get_db)):
    """
    Called by reporter.py for every security event:
        domain_blocked, process_killed, vpn_detected,
        screenshot_blocked, hosts_tampered, security_alert
    Stores exactly the four columns your Event model has.
    """
    # Parse timestamp from reporter if provided, else stamp now
    ts = datetime.utcnow()
    if payload.timestamp:
        try:
            ts = datetime.strptime(payload.timestamp, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass  # fall back to utcnow

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
        "Event  %-22s  session=%-10s  detail=%s",
        event.event_type, event.session_id, event.detail[:80],
    )
    return OKResponse(message=f"event {event.id} recorded")


# ── GET /events ───────────────────────────────────────────────────────────────

@router.get("/events", response_model=EventListResponse)
def list_events(
    session_id: str | None  = Query(None, description="Filter by session_id"),
    event_type: str | None  = Query(None, description="Filter by event_type"),
    skip:       int         = Query(0,   ge=0),
    limit:      int         = Query(100, ge=1, le=500),
    db: DBSession = Depends(get_db),
):
    """
    Return events newest-first.
    Optionally filter by session_id and/or event_type.
    """
    q = db.query(EventModel)

    if session_id:
        q = q.filter(EventModel.session_id == session_id)
    if event_type:
        q = q.filter(EventModel.event_type == event_type)

    total  = q.count()
    events = (
        q.order_by(EventModel.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return EventListResponse(
        total  = total,
        events = [_to_response(e) for e in events],
    )


# ── GET /events/{id} ──────────────────────────────────────────────────────────

@router.get("/events/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: DBSession = Depends(get_db)):
    """Return a single event by its integer primary key."""
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    return _to_response(event)


# ── Internal helper ───────────────────────────────────────────────────────────

def _to_response(e: EventModel) -> EventResponse:
    """Map ORM row → Pydantic response. candidate_name not in model → empty."""
    return EventResponse(
        id             = e.id,
        session_id     = e.session_id,
        event_type     = e.event_type,
        detail         = e.detail,
        timestamp      = e.timestamp,
        candidate_name = "",   # not stored in this Event model
    )