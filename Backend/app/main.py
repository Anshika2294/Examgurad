"""
app/main.py — FastAPI application factory.

Creates the app, registers all routers, creates DB tables on startup.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
import csv, io

from app.database import engine, SessionLocal
from app.models import Base, Session as SessionModel, Event as EventModel
from app.routes import health, session, events, auth
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ── Lifespan — runs on startup / shutdown ─────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("InterviewGuard backend starting up...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")
    yield
    # Shutdown
    logger.info("InterviewGuard backend shutting down.")


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title       = "InterviewGuard API",
    description = "Secure exam session monitoring backend.",
    version     = "2.0.0",
    lifespan    = lifespan,
)


# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow the dashboard (any origin in dev) to call the API.
# Tighten origins in production.

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(health.router)
app.include_router(session.router)
app.include_router(events.router)
app.include_router(auth.router)


@app.get("/dashboard")
def dashboard():
    return FileResponse("dashboard.html")


# ── CSV Export endpoints ──────────────────────────────────────────
# (duplicate copy that used to exist here has been removed —
#  these were previously defined twice, which caused the
#  "Duplicate Operation ID" warnings you saw on startup)

@app.get("/export/sessions")
def export_sessions():
    db = SessionLocal()
    rows = db.query(SessionModel).order_by(SessionModel.start_time.desc()).all()
    db.close()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["session_id", "candidate_name", "email", "started_at",
                "ended_at", "status", "event_count"])
    for s in rows:
        w.writerow([s.session_id, s.candidate_name, s.candidate_email,
                    s.start_time, s.end_time, s.status, len(s.events)])
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sessions.csv"},
    )


@app.get("/export/events")
def export_events():
    db = SessionLocal()
    rows = db.query(EventModel).order_by(EventModel.timestamp.desc()).all()
    db.close()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["timestamp", "session_id", "candidate_name", "event_type", "detail"])
    for e in rows:
        w.writerow([e.timestamp, e.session_id, e.candidate_name,
                    e.event_type, e.detail])
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=events.csv"},
    )
