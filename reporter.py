"""
reporter.py — Sends events from candidate machine to FastAPI backend
Place alongside main.py and blocker.py
"""

import threading, datetime, hashlib
try:
    import requests
except ImportError:
    import os, sys
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests

# ── CHANGE THIS to the interviewer's machine IP ──────────────────
SERVER = "http://localhost:8000"
# Example: SERVER = "http://192.168.1.42:8000"

TIMEOUT = 3

class Reporter:
    def __init__(self):
        self.session_id     = None
        self.candidate_name = ""
        self.candidate_email= ""
        self.role           = ""

    def _post(self, path, data):
        """Fire-and-forget — never blocks the main thread."""
        def _send():
            try:
                requests.post(f"{SERVER}{path}", json=data, timeout=TIMEOUT)
            except Exception as e:
                print(f"[Reporter] {path} failed: {e}")
        threading.Thread(target=_send, daemon=True).start()

    def _ts(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def start_session(self, name: str, email: str = "", role: str = ""):
        """Called by main.py do_start() — matches signature: reporter.start_session(name, email)"""
        self.candidate_name  = name
        self.candidate_email = email
        self.role            = role
        self.session_id      = hashlib.md5(
            f"{name}{datetime.datetime.now()}".encode()).hexdigest()[:8]
        self._post("/session/start", {
            "session_id":      self.session_id,
            "candidate_name":  name,
            "candidate_email": email,
            "role":            role,
            "timestamp":       self._ts(),
        })
        print(f"[Reporter] Session started: {self.session_id}")

    def end_session(self):
        if self.session_id:
            self._post("/session/end", {
                "session_id": self.session_id,
                "timestamp":  self._ts(),
            })
            print(f"[Reporter] Session ended: {self.session_id}")

    def domain_blocked(self, domain: str):
        self._post("/event", {
            "session_id":     self.session_id,
            "candidate_name": self.candidate_name,
            "role":           self.role,
            "event_type":     "domain_blocked",
            "detail":         domain,
            "timestamp":      self._ts(),
        })

    def process_killed(self, process_name: str):
        self._post("/event", {
            "session_id":     self.session_id,
            "candidate_name": self.candidate_name,
            "role":           self.role,
            "event_type":     "process_killed",
            "detail":         process_name,
            "timestamp":      self._ts(),
        })

    def vpn_detected(self, detail: str = ""):
        self._post("/event", {
            "session_id":     self.session_id,
            "candidate_name": self.candidate_name,
            "role":           self.role,
            "event_type":     "vpn_detected",
            "detail":         detail,
            "timestamp":      self._ts(),
        })

    def screenshot_blocked(self, detail: str = ""):
        self._post("/event", {
            "session_id":     self.session_id,
            "candidate_name": self.candidate_name,
            "role":           self.role,
            "event_type":     "screenshot_blocked",
            "detail":         detail,
            "timestamp":      self._ts(),
        })

# Singleton
reporter = Reporter()