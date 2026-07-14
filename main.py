"""
InterviewGuard v3.0 — Professional Tkinter Desktop App
Premium UI: sidebar nav, animated status, toast notifications,
            real-time security feed, modern card design.

Run as:
    Linux / macOS : sudo python3 main.py
    Windows       : run CMD/PowerShell as Administrator, then: python main.py
"""

import os, sys, threading, datetime, platform, hashlib, signal, subprocess, tempfile
import tkinter as tk
from tkinter import font as tkfont


try:    import psutil
except ImportError:
    os.system(f"{sys.executable} -m pip install psutil -q"); import psutil

import blocker
try:    from reporter import reporter
except Exception: reporter = None

OS       = platform.system()   # "Linux" | "Darwin" | "Windows"
LOCKFILE = os.path.join(tempfile.gettempdir(), "examguard.lock")
ADMIN_PASSWORD_HASH = hashlib.sha256(b"admin123").hexdigest()

def check_password(p): return hashlib.sha256(p.encode()).hexdigest() == ADMIN_PASSWORD_HASH

# ── Palette ──────────────────────────────────────────────────────
BG        = "#080E1A"
SIDEBAR   = "#0D1526"
SURFACE   = "#111C35"
CARD      = "#162040"
CARD2     = "#1A2650"
BORDER    = "#1E3060"
BORDER2   = "#243870"
ACCENT    = "#4F8EF7"
ACCENT2   = "#3D7BF0"
GREEN     = "#22D98A"
GREEN2    = "#1BC47D"
RED       = "#F75F5F"
RED2      = "#E54F4F"
AMBER     = "#F7C43A"
AMBER2    = "#E8B52E"
TEXT      = "#E2EAF8"
TEXT2     = "#B8C8E8"
MUTED     = "#4A5878"
MUTED2    = "#3A4868"
WHITE     = "#F0F6FF"
PURPLE    = "#9B72F5"
TEAL      = "#22D9C8"
NAVY      = "#0A1220"

# ── Fonts — pick something available on each OS ───────────────────
if OS == "Windows":
    _UI_FONT, _MONO_FONT = "Segoe UI", "Consolas"
elif OS == "Darwin":
    _UI_FONT, _MONO_FONT = "Helvetica Neue", "Menlo"
else:  # Linux
    _UI_FONT, _MONO_FONT = "Segoe UI", "Courier New"  # falls back to a default sans if missing

FONT_H1   = (_UI_FONT, 18, "bold")
FONT_H2   = (_UI_FONT, 14, "bold")
FONT_H3   = (_UI_FONT, 11, "bold")
FONT_BODY = (_UI_FONT, 10)
FONT_SM   = (_UI_FONT, 9)
FONT_XS   = (_UI_FONT, 8)
FONT_MONO = (_MONO_FONT, 9)

# ══════════════════════════════════════════════════════════════════
#  SECURITY HELPERS
# ══════════════════════════════════════════════════════════════════

def acquire_lockfile():
    if os.path.exists(LOCKFILE):
        try:
            with open(LOCKFILE) as f:
                pid = int(f.read().strip())
            if psutil.pid_exists(pid): return False
        except Exception: pass
    with open(LOCKFILE, 'w') as f: f.write(str(os.getpid()))
    return True

def release_lockfile():
    try: os.remove(LOCKFILE)
    except Exception: pass

def wipe_clipboard(root):
    try:
        root.clipboard_clear(); root.clipboard_append("")
        if OS == "Linux":
            # Tkinter's clipboard on Linux/X11 can linger after the app owns
            # the selection — clear it at the OS level too, if the tools exist.
            for cmd in [["xclip","-i","/dev/null"],["xsel","--clipboard","--delete"]]:
                try: subprocess.run(cmd, capture_output=True, timeout=2)
                except Exception: pass
        elif OS == "Darwin":
            subprocess.run(["pbcopy"], input=b"", timeout=2)
        elif OS == "Windows":
            # Tkinter's clipboard_clear()/append("") already clears the
            # Windows clipboard natively — no extra subprocess needed.
            pass
    except Exception: pass

def detect_vpn():
    keys = ['tun','tap','vpn','wg','proton','nord','express','pia','mullvad']
    try:
        return [i for i,s in psutil.net_if_stats().items()
                if s.isup and any(k in i.lower() for k in keys)]
    except Exception: return []

# Screenshot / screen-recording tools to kill, per OS.
SCREENSHOT_TOOL_PATTERNS = {
    "Linux": [
        'obs','kazam','recordmydesktop','simplescreenrecorder','vokoscreen',
        'peek','scrot','flameshot','shutter','gnome-screenshot','spectacle',
        'ksnip','screengrab',
    ],
    "Darwin": [
        'obs', 'screenshot', 'screencapture', 'grab', 'cleanshot',
        'shottr', 'snagit', 'capto',
    ],
    "Windows": [
        'obs', 'snippingtool', 'screensketch', 'screenclippinghost',
        'gamebar', 'gamebarpresencewriter', 'snagit', 'sharex', 'greenshot',
        'lightshot', 'picpick',
    ],
}

def kill_screenshot_tools():
    pats = SCREENSHOT_TOOL_PATTERNS.get(OS, SCREENSHOT_TOOL_PATTERNS["Linux"])
    killed = 0
    for proc in psutil.process_iter(['pid','name','exe']):
        try:
            n = (proc.info['name'] or '').lower()
            e = (proc.info['exe']  or '').lower()
            if any(p in n or p in e for p in pats):
                proc.kill(); killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied): pass
    return killed

def check_hosts_tamper():
    try:
        with open(blocker.HOSTS_PATH) as f: c = f.read()
        return blocker.MARKER_START not in c
    except Exception: return False

# ══════════════════════════════════════════════════════════════════
#  REUSABLE WIDGET HELPERS
# ══════════════════════════════════════════════════════════════════

def frm(parent, bg=None, **kw):
    return tk.Frame(parent, bg=bg or parent["bg"], **kw)

def lbl(parent, text, fg=TEXT, font=FONT_BODY, bg=None, **kw):
    return tk.Label(parent, text=text, fg=fg, font=font,
                    bg=bg or parent["bg"], **kw)

def sep(parent, bg=BORDER):
    return tk.Frame(parent, bg=bg, height=1)

def rounded_btn(parent, text, fg, cmd, bg=CARD, active_bg=CARD2,
                font=FONT_H3, padx=20, pady=8, cursor="hand2", bd=0):
    b = tk.Button(parent, text=text, fg=fg, bg=bg,
                  activebackground=active_bg, activeforeground=fg,
                  font=font, relief="flat", bd=bd, cursor=cursor,
                  command=cmd, padx=padx, pady=pady,
                  highlightthickness=1,
                  highlightbackground=fg,
                  highlightcolor=fg)
    return b

# ══════════════════════════════════════════════════════════════════
#  TOAST NOTIFICATION
# ══════════════════════════════════════════════════════════════════

class Toast(tk.Toplevel):
    def __init__(self, root, message, color=GREEN, duration=3000):
        super().__init__(root)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=CARD)

        # Position: bottom-right of root
        root.update_idletasks()
        rx = root.winfo_x() + root.winfo_width()
        ry = root.winfo_y() + root.winfo_height()
        self.geometry(f"320x52+{rx-340}+{ry-70}")

        # Border line on left
        tk.Frame(self, bg=color, width=4).pack(side="left", fill="y")

        inner = frm(self, bg=CARD)
        inner.pack(side="left", fill="both", expand=True, padx=12, pady=10)
        lbl(inner, message, fg=TEXT, font=FONT_SM, bg=CARD).pack(anchor="w")

        self.after(duration, self.destroy)
        # Fade in — skip on platforms where -alpha isn't supported well
        try:
            self.attributes("-alpha", 0.0)
            self._fade_in()
        except Exception:
            pass

    def _fade_in(self, alpha=0.0):
        alpha = min(alpha + 0.1, 0.95)
        try:
            self.attributes("-alpha", alpha)
            if alpha < 0.95:
                self.after(20, lambda: self._fade_in(alpha))
        except Exception: pass

# ══════════════════════════════════════════════════════════════════
#  PASSWORD DIALOG
# ══════════════════════════════════════════════════════════════════

class PasswordDialog(tk.Toplevel):
    def __init__(self, parent, title, on_success):
        super().__init__(parent)
        self._on_success = on_success
        self._attempts   = 0
        self.title(title)
        self.configure(bg=SURFACE)
        self.resizable(False, False)
        self.grab_set(); self.focus_set()
        w, h = 420, 260
        px = parent.winfo_x() + (parent.winfo_width()  - w) // 2
        py = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{px}+{py}")

        # Header bar
        hdr = frm(self, bg=CARD)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=ACCENT, height=3).pack(fill="x")
        lbl(hdr, title, fg=WHITE, font=FONT_H2, bg=CARD).pack(pady=(14,14), padx=20, anchor="w")

        body = frm(self, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=24, pady=10)

        lbl(body, "Admin password required to continue", fg=MUTED, font=FONT_SM,
            bg=SURFACE).pack(anchor="w", pady=(0,8))

        self._pwd = tk.StringVar()
        ef = frm(body, bg=BORDER, highlightthickness=0)
        ef.pack(fill="x", ipady=1)
        entry = tk.Entry(ef, textvariable=self._pwd, show="●",
                         bg=CARD, fg=TEXT, insertbackground=ACCENT,
                         relief="flat", font=(_UI_FONT, 12),
                         highlightthickness=0)
        entry.pack(fill="x", padx=1, pady=1, ipady=8)
        entry.bind("<Return>", lambda e: self._check())
        entry.focus_set()

        self._err = lbl(body, "", fg=RED, font=FONT_SM, bg=SURFACE)
        self._err.pack(anchor="w", pady=(4,0))

        btns = frm(body, bg=SURFACE)
        btns.pack(fill="x", pady=(10,0))
        rounded_btn(btns, "Cancel", MUTED, self.destroy, bg=SURFACE,
                    active_bg=CARD).pack(side="left", expand=True, fill="x", padx=(0,6))
        rounded_btn(btns, "Confirm", GREEN, self._check, bg=CARD2,
                    active_bg=CARD).pack(side="right", expand=True, fill="x", padx=(6,0))

    def _check(self):
        self._attempts += 1
        if check_password(self._pwd.get()):
            self.destroy(); self._on_success()
        else:
            left = 3 - self._attempts
            if left <= 0:
                self._err.config(text="✕  Too many attempts — locked")
            else:
                self._err.config(text=f"✕  Wrong password — {left} attempt(s) left")
            self._pwd.set("")

# ══════════════════════════════════════════════════════════════════
#  STAT CARD WIDGET
# ══════════════════════════════════════════════════════════════════

class StatCard(tk.Frame):
    def __init__(self, parent, value, label, color, icon="", **kw):
        super().__init__(parent, bg=CARD,
                         highlightthickness=1, highlightbackground=BORDER2,
                         **kw)
        # Top accent bar
        tk.Frame(self, bg=color, height=3).pack(fill="x")

        inner = frm(self, bg=CARD)
        inner.pack(fill="both", expand=True, padx=16, pady=12)

        top = frm(inner, bg=CARD)
        top.pack(fill="x")
        if icon:
            lbl(top, icon, fg=color, font=(_UI_FONT, 18), bg=CARD).pack(side="left")
        self._val = lbl(top, value, fg=color, font=(_UI_FONT, 22, "bold"), bg=CARD)
        self._val.pack(side="right")

        lbl(inner, label, fg=MUTED, font=FONT_XS, bg=CARD).pack(anchor="w", pady=(4,0))

    def set(self, v):
        self._val.config(text=str(v))

# ══════════════════════════════════════════════════════════════════
#  SECURITY EVENT FEED (live log in UI)
# ══════════════════════════════════════════════════════════════════

class EventFeed(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=CARD,
                         highlightthickness=1, highlightbackground=BORDER2,
                         **kw)
        tk.Frame(self, bg=ACCENT, height=3).pack(fill="x")

        hdr = frm(self, bg=CARD)
        hdr.pack(fill="x", padx=14, pady=(10,4))
        lbl(hdr, "⚡  LIVE SECURITY FEED", fg=ACCENT, font=FONT_XS, bg=CARD).pack(side="left")
        self._count_lbl = lbl(hdr, "0 events", fg=MUTED, font=FONT_XS, bg=CARD)
        self._count_lbl.pack(side="right")

        sep(self, BORDER).pack(fill="x")

        self._canvas = tk.Canvas(self, bg=CARD, highlightthickness=0, height=120)
        self._sb     = tk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._sb.set)
        self._sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._inner = frm(self._canvas, bg=CARD)
        self._win   = self._canvas.create_window((0,0), window=self._inner, anchor="nw")
        self._inner.bind("<Configure>", self._on_configure)
        self._canvas.bind("<Configure>", self._on_canvas_resize)

        self._events = []
        self._count  = 0

    def _on_configure(self, e):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_resize(self, e):
        self._canvas.itemconfig(self._win, width=e.width)

    def add(self, msg, color=TEXT2):
        ts   = datetime.datetime.now().strftime("%H:%M:%S")
        row  = frm(self._inner, bg=CARD)
        row.pack(fill="x", padx=10, pady=1)

        dot  = tk.Frame(row, bg=color, width=6, height=6)
        dot.pack(side="left", padx=(0,8), pady=6)
        lbl(row, ts, fg=MUTED, font=FONT_MONO, bg=CARD).pack(side="left")
        lbl(row, msg, fg=color, font=FONT_XS, bg=CARD,
            wraplength=300, justify="left").pack(side="left", padx=(6,0))

        self._count += 1
        self._count_lbl.config(text=f"{self._count} event{'s' if self._count != 1 else ''}")
        self._inner.update_idletasks()
        self._canvas.yview_moveto(1.0)

# ══════════════════════════════════════════════════════════════════
#  THREAT BADGE
# ══════════════════════════════════════════════════════════════════

class ThreatBadge(tk.Frame):
    def __init__(self, parent, icon, title, detail, color, **kw):
        super().__init__(parent, bg=CARD,
                         highlightthickness=1, highlightbackground=BORDER,
                         **kw)
        tk.Frame(self, bg=color, width=3).pack(side="left", fill="y")

        inner = frm(self, bg=CARD)
        inner.pack(fill="both", expand=True, padx=10, pady=8)

        top = frm(inner, bg=CARD)
        top.pack(fill="x")
        lbl(top, f"{icon} {title}", fg=TEXT, font=(_UI_FONT, 9, "bold"),
            bg=CARD).pack(side="left")
        badge = tk.Frame(top, bg=color, padx=4, pady=1)
        badge.pack(side="right")
        lbl(badge, "BLOCKED", fg=NAVY, font=(_UI_FONT, 7, "bold"), bg=color).pack()

        lbl(inner, detail, fg=MUTED, font=FONT_XS, bg=CARD,
            wraplength=180, justify="left").pack(anchor="w", pady=(3,0))

# ══════════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════════

class InterviewGuardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("InterviewGuard — Secure Exam Environment")
        self.configure(bg=BG)
        self.geometry("1040x680")
        self.minsize(920, 600)

        # State
        self.session_active  = False
        self.timer_seconds   = 0
        self._timer_after    = None
        self._watchdog_after = None
        self.kill_count      = 0
        self._pulse_after    = None
        self._pulse_state    = True

        # Log file
        log_dir = os.path.expanduser("~/.examguard")
        os.makedirs(log_dir, exist_ok=True)
        ts  = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self._log_path = os.path.join(log_dir, f"session_{ts}.log")
        self._log_file = open(self._log_path, 'a', buffering=1)
        self._log(f"InterviewGuard v3.0 started | PID={os.getpid()} | OS={OS}")

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        # SIGTERM isn't available on Windows — SIGINT (Ctrl+C) is.
        if OS != "Windows":
            signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        self.after(500, self._post_init)

    # ── UI BUILD ─────────────────────────────────────────────────

    def _build_ui(self):
        # Root layout: sidebar | main content
        root_row = frm(self, bg=BG)
        root_row.pack(fill="both", expand=True)

        self._build_sidebar(root_row)

        main = frm(root_row, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        self._build_topbar(main)
        sep(main, BORDER).pack(fill="x")
        self._build_content(main)

    def _build_sidebar(self, parent):
        sb = frm(parent, bg=SIDEBAR,
                 highlightthickness=1, highlightbackground=BORDER)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        sb.configure(width=220)

        # Logo area
        logo = frm(sb, bg=SIDEBAR)
        logo.pack(fill="x", pady=(0,0))
        tk.Frame(logo, bg=ACCENT, height=3).pack(fill="x")
        logo_inner = frm(logo, bg=SIDEBAR)
        logo_inner.pack(fill="x", padx=20, pady=18)

        # Shield icon simulation
        shield_frm = frm(logo_inner, bg=ACCENT, width=36, height=36)
        shield_frm.pack(side="left")
        shield_frm.pack_propagate(False)
        lbl(shield_frm, "🛡", font=(_UI_FONT, 18), fg=NAVY, bg=ACCENT).place(relx=0.5, rely=0.5, anchor="center")

        txt = frm(logo_inner, bg=SIDEBAR)
        txt.pack(side="left", padx=10)
        lbl(txt, "Interview", fg=WHITE, font=(_UI_FONT, 12, "bold"), bg=SIDEBAR).pack(anchor="w")
        lbl(txt, "Guard", fg=ACCENT, font=(_UI_FONT, 12, "bold"), bg=SIDEBAR).pack(anchor="w")

        sep(sb, BORDER).pack(fill="x", pady=(0,8))

        # Status section
        status_card = frm(sb, bg=CARD,
                          highlightthickness=1, highlightbackground=BORDER)
        status_card.pack(fill="x", padx=12, pady=4)
        tk.Frame(status_card, bg=GREEN, height=2).pack(fill="x")
        sc_inner = frm(status_card, bg=CARD)
        sc_inner.pack(fill="x", padx=12, pady=10)
        lbl(sc_inner, "SYSTEM STATUS", fg=MUTED, font=FONT_XS, bg=CARD).pack(anchor="w")
        status_row = frm(sc_inner, bg=CARD)
        status_row.pack(fill="x", pady=(6,0))
        self._sb_dot  = lbl(status_row, "●", fg=GREEN, font=(_UI_FONT, 14, "bold"), bg=CARD)
        self._sb_dot.pack(side="left")
        self._sb_status = lbl(status_row, "READY", fg=GREEN,
                               font=(_UI_FONT, 10, "bold"), bg=CARD)
        self._sb_status.pack(side="left", padx=(6,0))

        sep(sb, BORDER).pack(fill="x", pady=8)

        # Security checklist
        lbl(sb, "  SECURITY CHECKS", fg=MUTED, font=FONT_XS, bg=SIDEBAR).pack(anchor="w", pady=(0,6))
        checks = [
            ("🔒", "Hosts Blocking"),
            ("🧱", "Firewall Rules"),
            ("👁", "Process Monitor"),
            ("📋", "Clipboard Wipe"),
            ("🔍", "VPN Detection"),
            ("📸", "Screenshot Block"),
        ]
        self._check_labels = {}
        for icon, name in checks:
            row = frm(sb, bg=SIDEBAR)
            row.pack(fill="x", padx=12, pady=2)
            lbl(row, icon, fg=MUTED, font=FONT_XS, bg=SIDEBAR).pack(side="left")
            lbl(row, name, fg=MUTED, font=FONT_XS, bg=SIDEBAR).pack(side="left", padx=6)
            dot = lbl(row, "○", fg=MUTED, font=FONT_XS, bg=SIDEBAR)
            dot.pack(side="right")
            self._check_labels[name] = dot

        sep(sb, BORDER).pack(fill="x", pady=8)

        # Session info
        lbl(sb, "  SESSION INFO", fg=MUTED, font=FONT_XS, bg=SIDEBAR).pack(anchor="w", pady=(0,6))
        info_card = frm(sb, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        info_card.pack(fill="x", padx=12)
        ic = frm(info_card, bg=CARD)
        ic.pack(fill="x", padx=10, pady=10)

        def info_row(label, default):
            r = frm(ic, bg=CARD)
            r.pack(fill="x", pady=2)
            lbl(r, label, fg=MUTED, font=FONT_XS, bg=CARD).pack(side="left")
            v = lbl(r, default, fg=TEXT2, font=FONT_XS, bg=CARD)
            v.pack(side="right")
            return v

        self._info_name     = info_row("Candidate", "—")
        self._info_email    = info_row("Email", "—")
        self._info_started  = info_row("Started", "—")
        self._info_threats  = info_row("Threats", "0")

        # Bottom: version
        frm(sb, bg=SIDEBAR).pack(fill="y", expand=True)
        sep(sb, BORDER).pack(fill="x")
        lbl(sb, "  v3.0  •  Secure Build", fg=MUTED, font=FONT_XS,
            bg=SIDEBAR).pack(pady=10, anchor="w")

    def _build_topbar(self, parent):
        bar = frm(parent, bg=SURFACE)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        bar.configure(height=56)

        inner = frm(bar, bg=SURFACE)
        inner.pack(fill="both", expand=True, padx=24)

        lbl(inner, "Exam Session Control", fg=WHITE, font=FONT_H2,
            bg=SURFACE).pack(side="left", pady=14)

        # Right: OS + log path indicator
        right = frm(inner, bg=SURFACE)
        right.pack(side="right", pady=14)

        self._vpn_badge = lbl(right, "  VPN: None ✓  ", fg=GREEN,
                               font=FONT_XS, bg=CARD,
                               highlightthickness=1, highlightbackground=GREEN)
        self._vpn_badge.pack(side="right", padx=(8,0))

        self._tamper_badge = lbl(right, "  Hosts: Intact ✓  ", fg=GREEN,
                                  font=FONT_XS, bg=CARD,
                                  highlightthickness=1, highlightbackground=GREEN)
        self._tamper_badge.pack(side="right", padx=(8,0))

        lbl(right, f"  {OS}  ", fg=TEXT2, font=FONT_XS, bg=CARD2).pack(side="right", padx=(8,0))

    def _build_content(self, parent):
        content = frm(parent, bg=BG)
        content.pack(fill="both", expand=True, padx=24, pady=20)

        # ── Row 1: Candidate form + Stats ────────────────────────
        row1 = frm(content, bg=BG)
        row1.pack(fill="x", pady=(0,16))

        self._build_candidate_card(row1)
        self._build_stats_card(row1)

        # ── Row 2: Action buttons ─────────────────────────────────
        self._build_action_buttons(content)

        # ── Row 3: Threats grid + Event feed ─────────────────────
        row3 = frm(content, bg=BG)
        row3.pack(fill="both", expand=True, pady=(16,0))

        self._build_threats_grid(row3)
        self._build_event_feed(row3)

    def _build_candidate_card(self, parent):
        card = frm(parent, bg=CARD,
                   highlightthickness=1, highlightbackground=BORDER2)
        card.pack(side="left", fill="both", expand=True, padx=(0,12))
        tk.Frame(card, bg=ACCENT, height=3).pack(fill="x")

        inner = frm(card, bg=CARD)
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        lbl(inner, "CANDIDATE DETAILS", fg=ACCENT, font=FONT_XS, bg=CARD).pack(anchor="w")
        sep(inner, BORDER).pack(fill="x", pady=(6,12))

        def field(label_text, placeholder):
            f = frm(inner, bg=CARD)
            f.pack(fill="x", pady=(0,10))
            lbl(f, label_text, fg=TEXT2, font=(_UI_FONT, 9, "bold"),
                bg=CARD).pack(anchor="w", pady=(0,4))
            ef = frm(f, bg=BORDER2, highlightthickness=0)
            ef.pack(fill="x", ipady=1)
            entry = tk.Entry(ef, bg=CARD2, fg=TEXT, insertbackground=ACCENT,
                             relief="flat", font=(_UI_FONT, 11),
                             highlightthickness=0)
            entry.pack(fill="x", padx=10, pady=1, ipady=8)
            return entry

        self._name_entry  = field("Candidate Full Name  *", "e.g. Jane Smith")
        self._email_entry = field("Email Address  *",        "e.g. jane@company.com")

    def _build_stats_card(self, parent):
        card = frm(parent, bg=CARD,
                   highlightthickness=1, highlightbackground=BORDER2)
        card.pack(side="right", fill="y")
        card.pack_propagate(False)
        card.configure(width=280)
        tk.Frame(card, bg=GREEN, height=3).pack(fill="x")

        inner = frm(card, bg=CARD)
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        lbl(inner, "SESSION METRICS", fg=GREEN, font=FONT_XS, bg=CARD).pack(anchor="w")
        sep(inner, BORDER).pack(fill="x", pady=(6,12))

        g = frm(inner, bg=CARD)
        g.pack(fill="x")
        g.columnconfigure((0,1), weight=1)

        def mini_stat(parent, val, label, color, r, c):
            f = frm(parent, bg=CARD2,
                    highlightthickness=1, highlightbackground=BORDER)
            f.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")
            tk.Frame(f, bg=color, height=2).pack(fill="x")
            lbl(f, val, fg=color, font=(_UI_FONT, 16, "bold"), bg=CARD2).pack(pady=(8,2))
            lbl(f, label, fg=MUTED, font=FONT_XS, bg=CARD2).pack(pady=(0,8))

        self._stat_timer   = lbl(inner, "00:00:00", fg=ACCENT,
                                  font=(_UI_FONT, 28, "bold"), bg=CARD)
        self._stat_timer.pack()
        lbl(inner, "Session Duration", fg=MUTED, font=FONT_XS, bg=CARD).pack()

        sep(inner, BORDER).pack(fill="x", pady=10)

        g2 = frm(inner, bg=CARD)
        g2.pack(fill="x")
        g2.columnconfigure((0,1), weight=1)

        def sm(parent, val, ltext, color, r, c):
            f = frm(parent, bg=CARD2,
                    highlightthickness=1, highlightbackground=BORDER)
            f.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")
            vl = lbl(f, val, fg=color, font=(_UI_FONT, 14, "bold"), bg=CARD2)
            vl.pack(pady=(8,2))
            lbl(f, ltext, fg=MUTED, font=FONT_XS, bg=CARD2).pack(pady=(0,8))
            return vl

        self._stat_domains = sm(g2, str(len(blocker.DOMAINS)),  "Domains", GREEN,  0, 0)
        self._stat_apps    = sm(g2, str(len(blocker.KILL_PATTERNS)), "App Rules", PURPLE, 0, 1)
        self._stat_killed  = sm(g2, "0", "Killed", RED,    1, 0)
        self._stat_events  = sm(g2, "0", "Events", AMBER,  1, 1)

    def _build_action_buttons(self, parent):
        row = frm(parent, bg=BG)
        row.pack(fill="x")

        # Start button — large, prominent
        self._btn_start = tk.Button(
            row, text="▶   START EXAM SESSION",
            fg=NAVY, bg=GREEN, activebackground=GREEN2, activeforeground=NAVY,
            font=(_UI_FONT, 12, "bold"), relief="flat", bd=0,
            cursor="hand2", pady=12,
            command=self.do_start
        )
        self._btn_start.pack(side="left", expand=True, fill="x", padx=(0,8))

        # End button
        self._btn_end = tk.Button(
            row, text="■   END SESSION",
            fg=WHITE, bg=CARD, activebackground=RED2, activeforeground=WHITE,
            font=(_UI_FONT, 12, "bold"), relief="flat", bd=0,
            cursor="hand2", pady=12,
            highlightthickness=1, highlightbackground=RED,
            command=self.do_end
        )
        self._btn_end.pack(side="right", expand=True, fill="x", padx=(8,0))

    def _build_threats_grid(self, parent):
        card = frm(parent, bg=CARD,
                   highlightthickness=1, highlightbackground=BORDER2)
        card.pack(side="left", fill="both", expand=True, padx=(0,12))
        tk.Frame(card, bg=RED, height=3).pack(fill="x")

        inner = frm(card, bg=CARD)
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        hdr = frm(inner, bg=CARD)
        hdr.pack(fill="x", pady=(0,10))
        lbl(hdr, "BLOCKED THREAT CATEGORIES", fg=RED, font=FONT_XS, bg=CARD).pack(side="left")
        badge = tk.Frame(hdr, bg=RED, padx=6, pady=2)
        badge.pack(side="right")
        lbl(badge, f"{len(blocker.DOMAINS)} DOMAINS", fg=NAVY,
            font=(_UI_FONT, 7, "bold"), bg=RED).pack()

        sep(inner, BORDER).pack(fill="x", pady=(0,10))

        grid = frm(inner, bg=CARD)
        grid.pack(fill="both", expand=True)
        grid.columnconfigure((0,1,2), weight=1)

        threats = [
            ("🤖", "AI Assistants",    "ChatGPT · Claude · Gemini · Copilot · Grok",  RED),
            ("🎯", "Cheat Tools",      "LockedIn · Cluely · Parakeet · FinalRound",   RED),
            ("💻", "Coding Copilots",  "Cursor · Codeium · Tabnine · Phind",          RED),
            ("📖", "Homework / Q&A",   "Chegg · Brainly · WolframAlpha · CourseHero", AMBER),
            ("🖥️", "Local AI Apps",   "Ollama · LM Studio · Jan · KoboldAI",         AMBER),
            ("🔗", "Remote Access",    "AnyDesk · TeamViewer · Parsec · RustDesk",    AMBER),
        ]
        for i, (icon, title, detail, color) in enumerate(threats):
            ThreatBadge(grid, icon, title, detail, color).grid(
                row=i//3, column=i%3,
                padx=(0,6) if i%3 < 2 else 0,
                pady=(0,6), sticky="nsew"
            )

    def _build_event_feed(self, parent):
        self._feed = EventFeed(parent)
        self._feed.pack(side="right", fill="both")
        self._feed.pack_propagate(False)
        self._feed.configure(width=300)

    # ── HELPERS ──────────────────────────────────────────────────

    def _log(self, msg):
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try: self._log_file.write(f"[{ts}]  {msg}\n")
        except Exception: pass

    def _feed_event(self, msg, color=TEXT2):
        self.after(0, lambda: self._feed.add(msg, color))
        self._log(msg)
        # Increment event counter
        try:
            cur = int(self._stat_events.cget("text"))
            self._stat_events.config(text=str(cur + 1))
        except Exception: pass

    def _toast(self, msg, color=GREEN):
        self.after(0, lambda: Toast(self, msg, color))

    def _set_status(self, text, color):
        self._sb_dot.config(fg=color)
        self._sb_status.config(text=text, fg=color)

    def _set_check(self, name, ok=True):
        if name in self._check_labels:
            self._check_labels[name].config(
                text="●" if ok else "○",
                fg=GREEN if ok else MUTED
            )

    # ── TIMER ────────────────────────────────────────────────────

    def _tick(self):
        if not self.session_active: return
        self.timer_seconds += 1
        h = self.timer_seconds // 3600
        m = (self.timer_seconds % 3600) // 60
        s = self.timer_seconds % 60
        self._stat_timer.config(text=f"{h:02}:{m:02}:{s:02}")
        self._timer_after = self.after(1000, self._tick)

    def _start_timer(self):
        self.timer_seconds = 0; self._tick()

    def _stop_timer(self):
        if self._timer_after:
            self.after_cancel(self._timer_after); self._timer_after = None
        self._stat_timer.config(text="00:00:00")

    # ── PULSE ANIMATION (status dot) ─────────────────────────────

    def _start_pulse(self, color):
        self._pulse_state = True
        self._do_pulse(color)

    def _do_pulse(self, color):
        if not self.session_active: return
        self._pulse_state = not self._pulse_state
        c = color if self._pulse_state else MUTED
        try: self._sb_dot.config(fg=c)
        except Exception: return
        self._pulse_after = self.after(700, lambda: self._do_pulse(color))

    def _stop_pulse(self):
        if self._pulse_after:
            self.after_cancel(self._pulse_after); self._pulse_after = None

    # ── WATCHDOG ─────────────────────────────────────────────────

    def _watchdog(self):
        if not self.session_active: return

        def _run():
            # 1. Tamper
            if check_hosts_tamper():
                blocker.block()
                self._feed_event("[TAMPER] /etc/hosts modified — re-applied!", RED)
                self.after(0, lambda: self._tamper_badge.config(
                    text="  Hosts: TAMPERED ⚠  ", fg=RED, highlightbackground=RED))
                self._toast("⚠ Hosts tamper detected & fixed!", RED)
                if reporter: reporter.vpn_detected("hosts_tampered")
            else:
                self.after(0, lambda: self._tamper_badge.config(
                    text="  Hosts: Intact ✓  ", fg=GREEN, highlightbackground=GREEN))

            # 2. VPN
            vpns = detect_vpn()
            if vpns:
                msg = f"[VPN] Active interface: {', '.join(vpns)}"
                self._feed_event(msg, AMBER)
                self.after(0, lambda: self._vpn_badge.config(
                    text=f"  VPN: {vpns[0]} ⚠  ", fg=AMBER, highlightbackground=AMBER))
                if reporter: reporter.vpn_detected(', '.join(vpns))

            # 3. Screenshot tools
            sc = kill_screenshot_tools()
            if sc > 0:
                self.kill_count += sc
                self._feed_event(f"[SCREEN] {sc} screenshot tool(s) terminated", RED)
                self._update_killed()
                if reporter: reporter.screenshot_blocked(f"{sc} tools killed")

            # 4. Banned apps
            k2 = blocker.kill_apps()
            if k2 > 0:
                self.kill_count += k2
                self._feed_event(f"[PROCESS] {k2} banned app(s) killed by watchdog", RED)
                self._update_killed()
                if reporter: reporter.process_killed(f"{k2} apps killed by watchdog")

        threading.Thread(target=_run, daemon=True).start()
        self._watchdog_after = self.after(10000, self._watchdog)

    def _update_killed(self):
        self.after(0, lambda: (
            self._stat_killed.config(text=str(self.kill_count)),
            self._info_threats.config(text=str(self.kill_count))
        ))

    def _start_watchdog(self):
        self._watchdog_after = self.after(10000, self._watchdog)

    def _stop_watchdog(self):
        if self._watchdog_after:
            self.after_cancel(self._watchdog_after); self._watchdog_after = None

    # ── POST INIT ────────────────────────────────────────────────

    def _post_init(self):
        ok = blocker.check_privileges()
        if not ok:
            hint = "as Administrator" if OS == "Windows" else "with sudo"
            self._feed_event(f"[WARN] Not running {hint} — blocking will fail!", RED)
            self._toast(f"⚠ Run {hint} for full functionality", RED)
        else:
            self._feed_event(f"[OK] Admin privileges confirmed. PID={os.getpid()}", GREEN)

        self._feed_event(f"[OK] {len(blocker.DOMAINS)} domains ready to block", GREEN)
        self._feed_event(f"[OK] {len(blocker.KILL_PATTERNS)} process patterns loaded", GREEN)

        vpns = detect_vpn()
        if vpns:
            self._vpn_badge.config(text=f"  VPN: {vpns[0]} ⚠  ", fg=AMBER,
                                   highlightbackground=AMBER)
            self._feed_event(f"[VPN] Detected on startup: {', '.join(vpns)}", AMBER)
        else:
            self._feed_event("[OK] No VPN interfaces detected", GREEN)

        self._feed_event(f"[OK] Log: {self._log_path}", TEXT2)

    # ── INPUT LOCK ───────────────────────────────────────────────

    def _lock_inputs(self, locked):
        state = "disabled" if locked else "normal"
        self._name_entry.config(state=state)
        self._email_entry.config(state=state)
        if locked:
            self._btn_start.config(state="disabled", bg=MUTED2, fg=MUTED,
                                   highlightbackground=MUTED2)
        else:
            self._btn_start.config(state="normal", bg=GREEN, fg=NAVY,
                                   highlightbackground=GREEN)

    # ── START SESSION ────────────────────────────────────────────

    def do_start(self):
        if self.session_active: return

        name  = self._name_entry.get().strip()
        email = self._email_entry.get().strip()

        if not name:
            self._name_entry.focus_set()
            self._toast("⚠ Candidate Name is required", RED); return
        if not email:
            self._email_entry.focus_set()
            self._toast("⚠ Email Address is required", RED); return
        if "@" not in email or "." not in email.split("@")[-1]:
            self._email_entry.focus_set()
            self._toast("⚠ Please enter a valid email address", RED); return

        vpns = detect_vpn()
        if vpns:
            self._toast(f"⚠ Disable VPN first: {', '.join(vpns)}", RED); return

        if not blocker.check_privileges():
            hint = "as Administrator" if OS == "Windows" else "as sudo/admin"
            self._toast(f"⚠ Run {hint} for blocking to work", AMBER)

        self._lock_inputs(True)
        self._set_status("STARTING...", AMBER)
        self._feed_event(f"[START] Candidate: {name} | {email}", ACCENT)
        self.kill_count = 0
        self._stat_killed.config(text="0")
        self._stat_events.config(text="0")

        if reporter: reporter.start_session(name, email)

        def _run():
            try:
                wipe_clipboard(self)
                self._feed_event("[SECURITY] Clipboard wiped", GREEN)
                self._set_check("Clipboard Wipe", True)

                sc = kill_screenshot_tools()
                if sc:
                    self._feed_event(f"[SECURITY] {sc} screenshot tool(s) killed", RED)
                self._set_check("Screenshot Block", True)

                blocker.block(log_fn=lambda m: self._feed_event(m, TEXT2))
                if reporter:
                    reporter.domain_blocked(f"{len(blocker.DOMAINS)} domains blocked")

                self._set_check("Hosts Blocking", True)
                self._set_check("Firewall Rules", True)
                self._set_check("Process Monitor", True)
                self._set_check("VPN Detection", True)

                self.after(0, lambda n=name, e=email: self._on_start_done(n, e))
            except PermissionError:
                hint = "as Administrator" if OS == "Windows" else "as sudo!"
                self.after(0, lambda h=hint: self._start_failed(f"Permission denied — run {h}"))
            except Exception as ex:
                msg = str(ex)
                self.after(0, lambda m=msg: self._start_failed(m))

        threading.Thread(target=_run, daemon=True).start()

    def _start_failed(self, reason):
        self._log(f"[ERROR] {reason}")
        self._set_status("ERROR", RED)
        self._lock_inputs(False)
        self._toast(f"✕ {reason}", RED)

    def _on_start_done(self, name, email):
        self.session_active = True

        self._set_status("SESSION ACTIVE", GREEN)
        self._start_timer()
        self._start_pulse(GREEN)
        self._start_watchdog()

        # Update sidebar info
        self._info_name.config(text=name[:20] + ("…" if len(name) > 20 else ""))
        self._info_email.config(text=email[:22] + ("…" if len(email) > 22 else ""))
        self._info_started.config(text=datetime.datetime.now().strftime("%H:%M:%S"))

        # Style end button as active
        self._btn_end.config(bg=RED, fg=WHITE, activebackground=RED2)

        self._feed_event("[OK] Session active — all threats blocked", GREEN)
        self._toast("✓ Exam session started successfully!", GREEN)

    # ── END SESSION ──────────────────────────────────────────────

    def do_end(self):
        if not self.session_active: return
        PasswordDialog(self, "🔒  End Exam Session", self._do_end_confirmed)

    def _do_end_confirmed(self):
        h = self.timer_seconds // 3600
        m = (self.timer_seconds % 3600) // 60
        s = self.timer_seconds % 60
        self._log(f"[SESSION END] Duration: {h:02}:{m:02}:{s:02} | Killed: {self.kill_count}")
        self._set_status("UNBLOCKING...", AMBER)
        self._stop_watchdog()
        self._stop_pulse()
        if reporter: reporter.end_session()

        def _run():
            try:
                blocker.unblock(log_fn=lambda m: self._feed_event(m, TEXT2))
                self.after(0, self._on_end_done)
            except Exception as e:
                msg = str(e)
                self.after(0, lambda m=msg: self._feed_event(f"[ERROR] {m}", RED))

        threading.Thread(target=_run, daemon=True).start()

    def _on_end_done(self):
        self.session_active = False
        self._set_status("READY", GREEN)
        self._stop_timer()
        self._lock_inputs(False)

        # Reset inputs & sidebar info
        self._name_entry.delete(0, "end")
        self._email_entry.delete(0, "end")
        self._info_name.config(text="—")
        self._info_email.config(text="—")
        self._info_started.config(text="—")
        self._info_threats.config(text="0")

        # Reset checks
        for name in self._check_labels:
            self._set_check(name, False)

        # Reset end button style
        self._btn_end.config(bg=CARD, fg=WHITE, activebackground=RED2)
        self._tamper_badge.config(text="  Hosts: Intact ✓  ", fg=GREEN, highlightbackground=GREEN)
        self.kill_count = 0
        self._stat_killed.config(text="0")

        self._feed_event("[OK] Session ended — all restrictions removed", GREEN)
        self._toast("✓ Session ended. All restrictions removed.", GREEN)

    # ── CLOSE ────────────────────────────────────────────────────

    def _on_close(self):
        if self.session_active:
            PasswordDialog(self, "🔒  Close InterviewGuard", self._force_close)
        else:
            self._force_close()

    def _signal_handler(self, sig, frame):
        self._log(f"[SIGNAL] {sig} — cleaning up")
        self._force_close()

    def _force_close(self):
        self._stop_watchdog(); self._stop_timer(); self._stop_pulse()
        try: blocker.unblock()
        except Exception: pass
        try:
            if reporter: reporter.end_session()
        except Exception: pass
        try: self._log_file.close()
        except Exception: pass
        release_lockfile()
        self.destroy()


# ══════════════════════════════════════════════════════════════════
#  ENTRY
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if not acquire_lockfile():
        print("[ERROR] InterviewGuard is already running.")
        sys.exit(1)
    app = InterviewGuardApp()
    app.mainloop()