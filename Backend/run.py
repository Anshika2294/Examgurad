"""
run.py — Start the InterviewGuard FastAPI backend.

Usage
-----
    python run.py                        # default: 0.0.0.0:8000, reload on
    python run.py --host 192.168.1.10    # bind to specific IP (interviewer machine)
    python run.py --port 9000            # custom port
    python run.py --no-reload            # production — disable auto-reload

Environment variables
---------------------
    LOG_LEVEL   DEBUG | INFO | WARNING   (default: INFO)
    LOG_TO_FILE true | false             (default: true)
"""

import argparse
import uvicorn

from app.utils.logger import get_logger

logger = get_logger(__name__)


def parse_args():
    p = argparse.ArgumentParser(description="InterviewGuard backend server")
    p.add_argument("--host",      default="0.0.0.0",  help="Bind host (default: 0.0.0.0)")
    p.add_argument("--port",      default=8000, type=int, help="Bind port (default: 8000)")
    p.add_argument("--no-reload", action="store_true",   help="Disable auto-reload (production)")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()

    logger.info("=" * 60)
    logger.info("  InterviewGuard Backend v2.0.0")
    logger.info("  http://%s:%s", args.host, args.port)
    logger.info("  Docs  → http://%s:%s/docs", args.host, args.port)
    logger.info("  Health→ http://%s:%s/health", args.host, args.port)
    logger.info("=" * 60)

    uvicorn.run(
        "app.main:app",
        host      = args.host,
        port      = args.port,
        reload    = not args.no_reload,
        log_level = "warning",   # uvicorn access logs silenced — app logger handles it
    )