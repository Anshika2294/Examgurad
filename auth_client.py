"""
auth_client.py — Talks to the InterviewGuard FastAPI backend's auth endpoints.
Place alongside main.py, blocker.py, reporter.py.
"""

try:
    import requests
except ImportError:
    import os, sys
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests

from reporter import SERVER  # reuse the same backend URL as reporter.py

TIMEOUT = 6

# Holds the logged-in candidate's token/info for the current process
CURRENT_USER = {"token": None, "full_name": None, "email": None, "role": None}


class AuthError(Exception):
    """Raised with a user-friendly message on login/register failure."""
    pass


def _extract_error(resp) -> str:
    try:
        data = resp.json()
        detail = data.get("detail")
        if isinstance(detail, list):  # pydantic validation errors
            return "; ".join(e.get("msg", str(e)) for e in detail)
        if detail:
            return str(detail)
    except Exception:
        pass
    return f"Request failed ({resp.status_code})"


def login(email: str, password: str) -> dict:
    """Log a candidate in. Returns dict with token/full_name/email. Raises AuthError."""
    try:
        resp = requests.post(
            f"{SERVER}/auth/login",
            json={"email": email, "password": password},
            timeout=TIMEOUT,
        )
    except requests.exceptions.RequestException:
        raise AuthError("Cannot reach server. Check the backend is running.")

    if resp.status_code != 200:
        raise AuthError(_extract_error(resp))

    data = resp.json()
    CURRENT_USER.update({
        "token": data["access_token"],
        "full_name": data["full_name"],
        "email": data["email"],
        "role": data["role"],
    })
    return data


def register(full_name: str, email: str, password: str, confirm_password: str,
             university: str = "") -> dict:
    """Register a new candidate account. Returns the created user. Raises AuthError."""
    try:
        resp = requests.post(
            f"{SERVER}/auth/register",
            json={
                "full_name": full_name,
                "email": email,
                "password": password,
                "confirm_password": confirm_password,
                "university": university or None,
            },
            timeout=TIMEOUT,
        )
    except requests.exceptions.RequestException:
        raise AuthError("Cannot reach server. Check the backend is running.")

    if resp.status_code not in (200, 201):
        raise AuthError(_extract_error(resp))

    return resp.json()


def forgot_password(email: str) -> dict:
    try:
        resp = requests.post(
            f"{SERVER}/auth/forgot-password",
            json={"email": email},
            timeout=TIMEOUT,
        )
    except requests.exceptions.RequestException:
        raise AuthError("Cannot reach server. Check the backend is running.")

    if resp.status_code != 200:
        raise AuthError(_extract_error(resp))
    return resp.json()
