#!/usr/bin/env python3
# ============================================================
#  AI & Cheating Blocker — Universal (Linux / macOS / Windows)
#  Blocks websites AND kills desktop AI/cheating apps live.
#
#  Usage:
#    Linux/macOS : sudo python3 ai_block.py block
#                  sudo python3 ai_block.py unblock
#                  sudo python3 ai_block.py monitor   ← kills desktop apps live
#    Windows     : Run CMD/PowerShell as Administrator
#                  python ai_block.py block
#                  python ai_block.py unblock
#                  python ai_block.py monitor         ← kills desktop apps live
# ============================================================

import sys, os, subprocess, datetime, platform, time, signal

# ─────────────────────────────────────────────
#  AUTO-INSTALL psutil if missing
# ─────────────────────────────────────────────
try:
    import psutil
except ImportError:
    print("[!] Installing required module: psutil ...")
    os.system(f"{sys.executable} -m pip install psutil")
    import psutil

OS = platform.system()   # "Linux" | "Darwin" | "Windows"

# ─────────────────────────────────────────────
#  DOMAINS TO BLOCK (websites)
# ─────────────────────────────────────────────
DOMAINS = [
    # OpenAI / ChatGPT
    "chat.openai.com","chatgpt.com","openai.com","api.openai.com",
    # Anthropic / Claude
    "claude.ai","anthropic.com",
    # Google AI
    "gemini.google.com","bard.google.com","aistudio.google.com",
    # Microsoft Copilot
    "copilot.microsoft.com","bing.com","sydney.bing.com",
    # Meta AI
    "meta.ai","ai.meta.com",
    # Perplexity
    "perplexity.ai","www.perplexity.ai",
    # Grok / xAI
    "grok.x.ai","x.ai","grok.com","www.grok.com",
    # DeepSeek
    "chat.deepseek.com","deepseek.com",
    # Mistral
    "chat.mistral.ai","mistral.ai",
    # Cohere
    "coral.cohere.com","cohere.com",
    # HuggingFace
    "huggingface.co","huggingchat.co",
    # Poe / You
    "poe.com","you.com",
    # Pi AI
    "pi.ai","heypi.com",
    # Character.AI
    "character.ai","beta.character.ai",
    # Replika
    "replika.com","replika.ai",
    # Writing AI
    "jasper.ai","copy.ai","writesonic.com","rytr.me",
    # Paraphrasing / Grammar
    "quillbot.com","grammarly.com","app.grammarly.com","wordtune.com",
    # Image AI
    "runwayml.com","midjourney.com","stability.ai","dreamstudio.ai",
    # Coding AI
    "copilot.github.com","cursor.sh","codeium.com","tabnine.com","phind.com",
    # Interview cheating (web)
    "lockedinai.com","www.lockedinai.com","app.lockedinai.com",
    "interviewai.me","www.interviewai.me","app.interviewai.me",
    "interviewai.io","www.interviewai.io","app.interviewai.io",
    "prateek.ai","www.prateek.ai","app.prateek.ai",
    "beyz.ai","www.beyz.ai","app.beyz.ai","release.beyz.ai",
    "finalroundai.com","www.finalroundai.com","app.finalroundai.com",
    "d12araoe7z5xxk.cloudfront.net",
    "interviewcoder.co","www.interviewcoder.co","app.interviewcoder.co",
    "parakeetai.com","www.parakeetai.com","app.parakeetai.com",
    "parakeet-ai.com","www.parakeet-ai.com","app.parakeet-ai.com",
    "cluely.ai","www.cluely.ai","app.cluely.ai",
    "janitorai.com","www.janitorai.com",
    "crushon.ai","www.crushon.ai",
    "chai-research.com","chai.ml",
    "tavernai.com","www.tavernai.com",
    # Homework / essay cheating
    "chegg.com","www.chegg.com",
    "coursehero.com","www.coursehero.com",
    "studocu.com","www.studocu.com",
    "bartleby.com","www.bartleby.com",
    "homeworkify.eu","brainly.com","mathway.com",
    "wolframalpha.com","photomath.net","socratic.org","numerade.com",
    "edubirdie.com","paperhelp.org","grademiners.com","studybay.com",
]

# ─────────────────────────────────────────────
#  DESKTOP AI/CHEATING APPS TO KILL
#  (process name substring match, case-insensitive)
# ─────────────────────────────────────────────
KILL_PROCESS_PATTERNS = [
    # ── Interview cheating ──────────────────
    "lockedinai",
    "locked-in",
    "lockedin",
    "interviewcoder",
    "interview-coder",
    "finalroundai",
    "finalround",
    "final-round",
    "prateek",
    "beyzai",
    "beyz",
    "parakeet",          # catches Parakeet.ai desktop app
    "parakeetai",
    "parakeet-ai",
    "cluely",            # catches Cluely desktop app
    "cluelyai",
    "ghostwriter",
    "ghost-writer",
    "intervue",
    "interviewai",
    "aiinterview",
    "screenshotai",
    "codeshadow",
    "codeghost",
    "aiscribe",
    "copilot-interview",
    "hirevue-bypass",
    "examhelper",
    "answergpt",
    "gptanswer",

    # ── Screen overlay / hidden windows ─────
    "screenoverlay",
    "overlayapp",
    "hiddenbrowser",
    "stealthbrowser",
    "invisiblebrowser",
    "silentbrowser",
    "aiprompt",
    "promptassist",

    # ── Local AI servers ────────────────────
    "ollama",            # local LLM server
    "lmstudio",          # LM Studio
    "jan",               # Jan.ai desktop
    "oobabooga",
    "textgenwebui",
    "koboldai",

    # ── General AI desktop apps ─────────────
    "perplexity",        # Perplexity desktop
    "chatgpt",           # ChatGPT desktop app
    "copilot",           # MS Copilot standalone
]

# Exact exe names per OS for more precise matching
EXACT_NAMES = {
    "Windows": [
        "LockedInAI.exe", "lockedinai.exe",
        "InterviewCoder.exe", "interviewcoder.exe",
        "FinalRoundAI.exe", "finalroundai.exe",
        "Prateek.exe", "prateek.exe",
        "BeyzAI.exe", "beyzai.exe",
        "Parakeet.exe", "parakeet.exe", "ParakeetAI.exe",
        "Cluely.exe", "cluely.exe",
        "GhostWriter.exe",
        "Ollama.exe", "ollama.exe",
        "LMStudio.exe", "lmstudio.exe",
        "jan.exe",
        "ChatGPT.exe",
    ],
    "Darwin": [
        "LockedIn AI", "InterviewCoder", "Final Round AI",
        "Parakeet", "Parakeet AI",
        "Cluely",
        "Ollama", "LM Studio", "Jan",
        "ChatGPT",
    ],
    "Linux": [
        "lockedinai", "interviewcoder", "finalroundai",
        "parakeet", "cluely", "ollama", "lmstudio", "jan",
    ],
}

# ─────────────────────────────────────────────
#  HARDCODED IP RANGES
# ─────────────────────────────────────────────
BLOCK_IPS = [
    "66.33.60.0/24","76.76.21.0/24","216.150.1.0/24","216.150.16.0/24",
    "13.248.169.0/24","76.223.54.0/24","54.230.141.0/24","199.36.158.0/24",
    "104.26.2.0/24","104.26.3.0/24","172.67.213.0/24","104.21.53.0/24",
    "172.67.219.0/24","104.21.24.0/24","172.67.222.0/24","104.21.54.0/24",
]

# ─────────────────────────────────────────────
#  OS-SPECIFIC PATHS
# ─────────────────────────────────────────────
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts" if OS == "Windows" else "/etc/hosts"
MARK_START = "# ===== AI_BLOCKER_START ====="
MARK_END   = "# ===== AI_BLOCKER_END ====="

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def run(cmd, shell=False):
    return subprocess.run(cmd, capture_output=True, text=True, shell=shell)

def ts():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log(msg):
    print(f"[{ts()}] {msg}", flush=True)

def flush_dns():
    print("  Flushing DNS cache...")
    if OS == "Linux":
        for svc in ["systemd-resolved","nscd","dnsmasq"]:
            if run(["systemctl","restart",svc]).returncode == 0:
                print(f"  DNS flushed via {svc}."); break
    elif OS == "Darwin":
        run(["dscacheutil","-flushcache"])
        run(["killall","-HUP","mDNSResponder"])
        print("  DNS flushed (macOS).")
    elif OS == "Windows":
        run("ipconfig /flushdns", shell=True)
        print("  DNS flushed (Windows).")

def resolve_ips(domain):
    ips = set()
    if OS == "Windows":
        r = run(f"nslookup {domain}", shell=True)
        if r.returncode == 0:
            for line in r.stdout.splitlines():
                line = line.strip()
                if line.startswith("Address:") and "#" not in line:
                    ip = line.replace("Address:","").strip()
                    if ip: ips.add(ip)
    else:
        r = run(["dig","+short",domain])
        if r.returncode == 0:
            for line in r.stdout.strip().splitlines():
                line = line.strip()
                if line and not line.endswith("."): ips.add(line)
        if not ips:
            r = run(["host",domain])
            if r.returncode == 0:
                for line in r.stdout.strip().splitlines():
                    if "has address" in line:
                        ips.add(line.split("has address")[-1].strip())
    return ips

# ─────────────────────────────────────────────
#  HOSTS FILE
# ─────────────────────────────────────────────
def update_hosts_block():
    print(f"\n[HOSTS] Updating {HOSTS_PATH} ...")
    with open(HOSTS_PATH,"r") as f: content = f.read()
    if MARK_START not in content:
        lines = [f"\n{MARK_START}", f"# Added {ts()}"]
        for d in DOMAINS: lines.append(f"0.0.0.0  {d}")
        lines.append(MARK_END)
        with open(HOSTS_PATH,"a") as f: f.write("\n".join(lines)+"\n")
        print(f"  {len(DOMAINS)} domains added.")
    else:
        print("  Hosts file already updated.")

def remove_hosts_block():
    print(f"\n[HOSTS] Cleaning {HOSTS_PATH} ...")
    with open(HOSTS_PATH,"r") as f: content = f.read()
    if MARK_START in content:
        s = content.find(MARK_START)
        e = content.find(MARK_END)+len(MARK_END)
        new = content[:s].rstrip()+"\n"+content[e:].lstrip()
        with open(HOSTS_PATH,"w") as f: f.write(new)
        print("  Hosts file cleaned.")
    else:
        print("  Nothing to remove.")

# ─────────────────────────────────────────────
#  LINUX — iptables
# ─────────────────────────────────────────────
LINUX_COMMENT_FW = "AI_BLOCKER"
LINUX_COMMENT_IP = "AI_IP_BLOCKER"

def linux_block_firewall():
    print(f"\n[FIREWALL/Linux] Blocking domains via iptables...")
    r = run(["iptables","-L","OUTPUT","-n"])
    if LINUX_COMMENT_FW not in r.stdout:
        blocked = 0
        for domain in DOMAINS:
            ips = resolve_ips(domain)
            for ip in ips:
                run(["iptables","-A","OUTPUT","-d",ip,"-m","comment","--comment",LINUX_COMMENT_FW,"-j","DROP"])
                run(["iptables","-A","INPUT", "-s",ip,"-m","comment","--comment",LINUX_COMMENT_FW,"-j","DROP"])
            if ips: blocked += 1
        for domain in DOMAINS:
            run(["iptables","-A","OUTPUT","-p","udp","--dport","53",
                 "-m","string","--string",domain,"--algo","bm",
                 "-m","comment","--comment",LINUX_COMMENT_FW,"-j","DROP"])
        print(f"  {blocked} domains blocked.")
    else:
        print("  Domain rules already active.")
    r = run(["iptables","-L","OUTPUT","-n"])
    if LINUX_COMMENT_IP not in r.stdout:
        for ip in BLOCK_IPS:
            run(["iptables","-A","OUTPUT","-d",ip,"-m","comment","--comment",LINUX_COMMENT_IP,"-j","DROP"])
            run(["iptables","-A","INPUT", "-s",ip,"-m","comment","--comment",LINUX_COMMENT_IP,"-j","DROP"])
    os.makedirs("/etc/iptables",exist_ok=True)
    rules = run(["iptables-save"])
    with open("/etc/iptables/rules.v4","w") as f: f.write(rules.stdout)
    print("  Rules saved persistently.")

def linux_unblock_firewall():
    for comment in [LINUX_COMMENT_FW, LINUX_COMMENT_IP]:
        removed = 0
        for chain in ["OUTPUT","INPUT"]:
            while True:
                r = run(["iptables","-L",chain,"-n","--line-numbers"])
                found = False
                for line in r.stdout.splitlines():
                    if comment in line:
                        run(["iptables","-D",chain,line.split()[0]])
                        removed += 1; found = True; break
                if not found: break
        print(f"  Removed {removed} rules [{comment}].")
    rules = run(["iptables-save"])
    with open("/etc/iptables/rules.v4","w") as f: f.write(rules.stdout)

# ─────────────────────────────────────────────
#  macOS — pf
# ─────────────────────────────────────────────
PF_ANCHOR      = "ai_blocker"
PF_ANCHOR_FILE = f"/etc/pf.anchors/{PF_ANCHOR}"
PF_CONF        = "/etc/pf.conf"
PF_REF_LINE    = f'anchor "{PF_ANCHOR}"'
PF_LOAD_LINE   = f'load anchor "{PF_ANCHOR}" from "{PF_ANCHOR_FILE}"'

def macos_block_firewall():
    print(f"\n[FIREWALL/macOS] Setting up pf anchor...")
    all_ips = set(BLOCK_IPS)
    for domain in DOMAINS: all_ips.update(resolve_ips(domain))
    lines = ["# AI Blocker pf rules\n"]
    for ip in all_ips:
        lines.append(f'block drop out quick to {ip}\n')
        lines.append(f'block drop in  quick from {ip}\n')
    os.makedirs("/etc/pf.anchors",exist_ok=True)
    with open(PF_ANCHOR_FILE,"w") as f: f.writelines(lines)
    with open(PF_CONF,"r") as f: pf = f.read()
    if PF_REF_LINE not in pf:  pf += f'\n{PF_REF_LINE}\n'
    if PF_LOAD_LINE not in pf: pf += f'{PF_LOAD_LINE}\n'
    with open(PF_CONF,"w") as f: f.write(pf)
    run(["pfctl","-e"]); run(["pfctl","-f",PF_CONF])
    print("  pf firewall enabled.")

def macos_unblock_firewall():
    if os.path.exists(PF_ANCHOR_FILE): os.remove(PF_ANCHOR_FILE)
    with open(PF_CONF,"r") as f: lines = f.readlines()
    with open(PF_CONF,"w") as f:
        f.writelines([l for l in lines if PF_REF_LINE not in l and PF_LOAD_LINE not in l])
    run(["pfctl","-f",PF_CONF])
    print("  pf firewall cleaned.")

# ─────────────────────────────────────────────
#  WINDOWS — netsh
# ─────────────────────────────────────────────
WIN_RULE_PREFIX = "AI_BLOCKER_"

def windows_block_firewall():
    print(f"\n[FIREWALL/Windows] Adding firewall rules...")
    all_ips = set(BLOCK_IPS)
    for domain in DOMAINS: all_ips.update(resolve_ips(domain))
    for i,ip in enumerate(all_ips):
        run(f'netsh advfirewall firewall add rule name="{WIN_RULE_PREFIX}{i}" dir=out action=block remoteip={ip}', shell=True)
        run(f'netsh advfirewall firewall add rule name="{WIN_RULE_PREFIX}{i}_in" dir=in action=block remoteip={ip}', shell=True)
    print(f"  {len(all_ips)} IPs blocked.")

def windows_unblock_firewall():
    r = run('netsh advfirewall firewall show rule name=all', shell=True)
    removed = 0
    for line in r.stdout.splitlines():
        if line.startswith("Rule Name:"):
            rule = line.replace("Rule Name:","").strip()
            if rule.startswith(WIN_RULE_PREFIX):
                run(f'netsh advfirewall firewall delete rule name="{rule}"', shell=True)
                removed += 1
    print(f"  Removed {removed} firewall rules.")

# ─────────────────────────────────────────────
#  DESKTOP APP KILLER — real-time monitor
# ─────────────────────────────────────────────
killed_pids = set()

def is_ai_app(proc):
    """Return True if this process is a known AI/cheating desktop app."""
    try:
        name    = proc.name().lower()
        cmdline = " ".join(proc.cmdline()).lower()
        exe     = (proc.exe() or "").lower()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False

    # Substring match
    for pattern in KILL_PROCESS_PATTERNS:
        p = pattern.lower()
        if p in name or p in cmdline or p in exe:
            return True

    # Exact match for current OS
    for exact in EXACT_NAMES.get(OS, []):
        if exact.lower() == name:
            return True

    return False

def kill_ai_apps(verbose=True):
    """Scan all processes and kill AI/cheating apps. Returns count killed."""
    count = 0
    for proc in psutil.process_iter(['pid','name']):
        if proc.pid in killed_pids:
            continue
        if is_ai_app(proc):
            try:
                name = proc.name()
                pid  = proc.pid
                proc.kill()
                killed_pids.add(pid)
                log(f"[KILLED] {name}  (PID {pid})")
                count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    return count

def monitor_loop(interval=2):
    """Run forever, killing AI apps the moment they appear."""
    log(f"[MONITOR] Real-time desktop app killer started (scan every {interval}s)")
    log("[MONITOR] Press Ctrl+C to stop.\n")
    try:
        while True:
            count = kill_ai_apps(verbose=True)
            if count == 0:
                # Heartbeat every ~30s
                now = datetime.datetime.now()
                if now.second < interval:
                    print(f"\r[{ts()}] Watching... no threats detected", end="", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        print()
        log("[MONITOR] Stopped.")

# ─────────────────────────────────────────────
#  PRIVILEGE CHECK
# ─────────────────────────────────────────────
def check_privileges():
    if OS == "Windows":
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    else:
        return os.geteuid() == 0

# ─────────────────────────────────────────────
#  BLOCK
# ─────────────────────────────────────────────
def block(log_fn=print):
    log_fn("=" * 60)
    log_fn(f"  AI & CHEATING BLOCKER — BLOCKING [{OS}]")
    log_fn("=" * 60)

    # 1. Kill any already-running desktop AI apps immediately
    log_fn("[DESKTOP] Killing any running AI/cheating apps now...")
    count = kill_ai_apps()
    log_fn(f"  {count} app(s) killed.")

    # 2. Block websites via hosts file
    update_hosts_block()
    flush_dns()

    # 3. Block via firewall
    if OS == "Linux":      linux_block_firewall()
    elif OS == "Darwin":   macos_block_firewall()
    elif OS == "Windows":  windows_block_firewall()

    log_fn("  WEBSITES BLOCKED + DESKTOP APPS KILLED.")
    log_fn("  → Chrome: chrome://net-internals/#dns → Clear host cache")

# ─────────────────────────────────────────────
#  UNBLOCK
# ─────────────────────────────────────────────
def unblock(log_fn=print):
    log_fn("=" * 60)
    log_fn(f"  AI & CHEATING BLOCKER — UNBLOCKING [{OS}]")
    log_fn("=" * 60)

    remove_hosts_block()
    flush_dns()

    if OS == "Linux":
        log_fn("[FIREWALL/Linux] Removing firewall rules...")
        linux_unblock_firewall()
    elif OS == "Darwin":   macos_unblock_firewall()
    elif OS == "Windows":  windows_unblock_firewall()

    log_fn("  ALL DONE. Everything is unblocked.")

# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def usage():
    print(f"\nAI & Cheating Blocker — Universal [{OS}]")
    print("\nCommands:")
    cmd = "python ai_block.py" if OS == "Windows" else "sudo python3 ai_block.py"
    print(f"  {cmd} block     → Block websites + kill desktop AI apps")
    print(f"  {cmd} unblock   → Remove all blocks")
    print(f"  {cmd} monitor   → Real-time desktop app killer (runs forever)")
    print(f"  {cmd} kill      → Kill desktop AI apps once and exit")
    if OS != "Windows":
        print("\n  (Must be run with sudo)")
    else:
        print("\n  (Must run CMD/PowerShell as Administrator)")

# ─────────────────────────────────────────────
#  ALIASES — for main.py compatibility
# ─────────────────────────────────────────────
KILL_PATTERNS  = KILL_PROCESS_PATTERNS
kill_apps      = kill_ai_apps
MARKER_START   = MARK_START   # alias used by main.py tamper detection

if __name__ == '__main__':
    if not check_privileges():
        print("ERROR: Run with sudo (Linux/macOS) or as Administrator (Windows).")
        sys.exit(1)

    COMMANDS = ("block","unblock","monitor","kill")
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        usage()
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "block":    block()
    elif cmd == "unblock": unblock()
    elif cmd == "monitor": monitor_loop()
    elif cmd == "kill":
        print("[DESKTOP] Scanning for AI/cheating apps...")
        count = kill_ai_apps()
        print(f"[DONE] {count} app(s) killed.")