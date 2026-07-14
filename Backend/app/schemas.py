"""
app/schemas.py — Pydantic v2 request / response models.
Mirrors exactly what reporter.py sends over the wire.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ── Shared ────────────────────────────────────────────────────────────────────

class OKResponse(BaseModel):
    status:  str = "ok"
    message: str = ""


# ── Session ───────────────────────────────────────────────────────────────────

class SessionStartRequest(BaseModel):
    """POST /session/start — sent by reporter.py → Reporter.start_session()"""
    session_id:      str           = Field(..., min_length=1, max_length=16)
    candidate_name:  str           = Field(..., min_length=1, max_length=128)
    candidate_email: str           = Field("",  max_length=256)
    role:            str           = Field("",  max_length=128)
    event_type:      str           = Field("session_start")
    detail:          str           = Field("")
    timestamp:       Optional[str] = None


class SessionEndRequest(BaseModel):
    """POST /session/end — sent by reporter.py → Reporter.end_session()"""
    session_id:       str          = Field(..., min_length=1, max_length=16)
    candidate_name:   str          = Field("",  max_length=128)
    candidate_email:  str          = Field("",  max_length=256)
    event_type:       str          = Field("session_end")
    detail:           str          = Field("")
    duration_seconds: int          = Field(0, ge=0)
    timestamp:        Optional[str] = None


class SessionResponse(BaseModel):
    """Full session record returned to the dashboard."""
    id:               int
    session_id:       str
    candidate_name:   str
    candidate_email:  str
    role:             str
    started_at:       datetime
    ended_at:         Optional[datetime]
    duration_seconds: Optional[int]
    is_active:        bool
    event_count:      int = 0

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    total:    int
    sessions: List[SessionResponse]


# ── Events ────────────────────────────────────────────────────────────────────

class EventRequest(BaseModel):
    """
    POST /event — sent by reporter.py for every security event.
    Matches _base_event() output exactly.
    """
    session_id:      str           = Field(..., min_length=1, max_length=16)
    candidate_name:  str           = Field("",  max_length=128)
    candidate_email: str           = Field("",  max_length=256)
    event_type:      str           = Field(..., min_length=1, max_length=64)
    detail:          str           = Field("")
    timestamp:       Optional[str] = None


class EventResponse(BaseModel):
    id:             int
    session_id:     str
    event_type:     str
    detail:         str
    timestamp:      datetime
    candidate_name: str

    model_config = {"from_attributes": True}


class EventListResponse(BaseModel):
    total:  int
    events: List[EventResponse]


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status:  str = "ok"
    version: str = "2.0.0"
    db:      str = "connected"