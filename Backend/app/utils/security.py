"""
app/utils/security.py — Password hashing + JWT helpers for InterviewGuard auth.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext

# ── Config (override via .env) ─────────────────────────────────────
SECRET_KEY   = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")
ALGORITHM    = "HS256"
ACCESS_EXPIRE_MINUTES = 60 * 24        # 24 hours
RESET_EXPIRE_MINUTES  = 30             # reset token short-lived

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


# ── Password hashing ─────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT creation ──────────────────────────────────────────────────────
def _create_token(data: dict, expires_minutes: int, token_type: str) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire, "type": token_type})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(user_id: int, email: str, role: str) -> str:
    return _create_token(
        {"sub": str(user_id), "email": email, "role": role},
        ACCESS_EXPIRE_MINUTES,
        "access",
    )


def create_reset_token(user_id: int, email: str) -> str:
    return _create_token(
        {"sub": str(user_id), "email": email},
        RESET_EXPIRE_MINUTES,
        "reset",
    )


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong token type",
        )
    return payload


# ── FastAPI dependencies ──────────────────────────────────────────────
def get_current_payload(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    return decode_token(creds.credentials, expected_type="access")


def require_role(role: str):
    """Dependency factory — use as Depends(require_role('admin'))."""
    def checker(payload: dict = Depends(get_current_payload)) -> dict:
        if payload.get("role") != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {role} role",
            )
        return payload
    return checker
