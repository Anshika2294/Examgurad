# ExamGuard

A secure exam-proctoring system with two parts:

1. **Backend** — FastAPI server that receives session/event data and serves an admin dashboard.
2. **Candidate App** — A desktop app (Tkinter) that candidates run on their own machine. It blocks AI/cheating websites and desktop tools during an exam session, and reports activity to the backend in real time.

---

## Project Structure

```
Examguard/
├── main.py              # Candidate desktop app (Tkinter GUI)
├── blocker.py            # Cross-platform website/app blocker (Linux/macOS/Windows)
├── reporter.py            # Sends session/event data to the backend
│
└── Backend/
    ├── run.py              # Starts the FastAPI backend
    ├── requirements.txt
    ├── dashboard.html        # Admin dashboard (served at /dashboard)
    └── app/
        ├── main.py             # FastAPI app factory, routes registration
        ├── models.py            # SQLAlchemy models (sessions, events)
        ├── database.py           # DB engine/session setup (SQLite)
        ├── schemas.py             # Pydantic request/response schemas
        ├── utils/
        │   └── logger.py
        ├── routes/
        │   ├── health.py
        │   ├── session.py
        │   └── events.py
        └── service/
            ├── session_event.py
            └── event_service.py
```

---

## How It Works

- The **candidate app** blocks 112+ AI/cheating domains (ChatGPT, Claude, Chegg, etc.) via the hosts file + firewall rules, and kills 47+ known cheating/AI desktop apps (Cluely, LockedIn AI, Ollama, etc.) in real time.
- It also detects VPNs, wipes the clipboard, blocks screenshot tools, and watches for tampering with the hosts file — reporting every event to the backend.
- The **backend** stores all sessions and events in a SQLite database and exposes a dashboard (`/dashboard`) with live session data and CSV export.

---

## Setup

### 1. Backend

```bash
cd Backend
pip install -r requirements.txt
python run.py
```

Runs on `http://localhost:8000` by default.

- Dashboard: `http://localhost:8000/dashboard`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 2. Candidate App

```bash
cd Examguard
```

**Linux / macOS:**
```bash
sudo python3 main.py
```

**Windows** (run CMD/PowerShell as Administrator):
```bash
python main.py
```

> Admin/root privileges are required — the app modifies the hosts file and firewall rules.

Before running elsewhere than your own machine, update the backend URL in `reporter.py`:

```python
SERVER = "http://127.0.0.1:8000"   # change to your deployed backend URL
```

---

## Usage

1. Start the backend (keep it running throughout the exam).
2. Launch the candidate app on the candidate's machine.
3. Enter **Candidate Full Name** and **Email Address**.
4. Click **START EXAM SESSION** — blocking begins immediately, and the session appears live on the dashboard.
5. Click **END SESSION** to stop — you'll be asked for the admin password (default: `admin123`, defined in `main.py` as `ADMIN_PASSWORD_HASH` — change this before real use).
6. Export session/event history as CSV anytime from `/dashboard` → Export Data.

---

## Deployment (Backend)

The backend can be deployed to any Python-friendly host (Render, Railway, etc.). Example for **Render**:

1. Push this repo to GitHub.
2. On Render: **New → Web Service** → connect the repo.
3. Settings:
   - **Root Directory:** `Backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python run.py --port $PORT --no-reload`
4. Deploy — you'll get a public URL (e.g. `https://yourapp.onrender.com`).
5. Update `SERVER` in `reporter.py` on every candidate machine to point to this URL.

> Free tiers on most hosts reset the filesystem on restart/sleep — the SQLite database will lose data unless you attach a persistent disk or switch to a hosted database (e.g. Postgres).

**Note:** The candidate app itself cannot be deployed to the cloud — it must run locally on each candidate's machine, since it modifies that machine's hosts file and firewall.

---

## Security Notes

- Change the default admin password (`admin123`) before any real use — it's hashed with SHA-256 in `main.py`.
- CORS is currently open (`allow_origins = ["*"]`) in `Backend/app/main.py` — tighten this before production/public deployment.
- The candidate app requires elevated privileges (sudo/Administrator) to modify system network settings — this is expected and required for blocking to work.

---

## Requirements

**Backend:** `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `python-dotenv` (see `Backend/requirements.txt`)

**Candidate App:** `psutil`, `requests` (auto-installed on first run if missing)
