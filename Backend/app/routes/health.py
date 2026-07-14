"""
routes/health.py — Health check endpoint.

GET /health  → called by reporter.py on startup to test connectivity
              reporter checks:  r.status_code == 200  → sets self.connected = True
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import text

from app.database import get_db
from app.schemas import HealthResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check(db: DBSession = Depends(get_db)):
    """
    Lightweight liveness + DB connectivity check.
    reporter.py hits this on startup — must return 200 to set connected = True.
    """
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error("DB health check failed: %s", e)
        db_status = "error"

    logger.debug("Health check  db=%s", db_status)

    return HealthResponse(
        status  = "ok",
        version = "2.0.0",
        db      = db_status,
    )