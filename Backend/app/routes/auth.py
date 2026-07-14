"""
app/routes/auth.py — Registration, login, forgot/reset password endpoints.
Students register via /auth/register. Admin accounts are NOT publicly
registrable — create them via a seed script (see create_admin.py) for security.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app.schemas_auth import (
    RegisterRequest, LoginRequest, TokenResponse, UserOut,
    ForgotPasswordRequest, ResetPasswordRequest,
)
from app.service import auth_service
from app.utils.security import (
    create_access_token, create_reset_token, decode_token,
    get_current_payload,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


# ── Student registration ───────────────────────────────────────────
@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DBSession = Depends(get_db)):
    user = auth_service.create_user(
        db, payload.full_name, payload.email, payload.password,
        university=payload.university, role="student",
    )
    logger.info("New student registered: %s", user.email)
    return user


# ── Student login ───────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DBSession = Depends(get_db)):
    user = auth_service.authenticate_user(
        db, payload.email, payload.password, expected_role="student",
    )
    token = create_access_token(user.id, user.email, user.role)
    return TokenResponse(
        access_token=token, role=user.role,
        full_name=user.full_name, email=user.email,
    )


# ── Admin login (separate endpoint, same table, role check) ────────
@router.post("/admin/login", response_model=TokenResponse)
def admin_login(payload: LoginRequest, db: DBSession = Depends(get_db)):
    user = auth_service.authenticate_user(
        db, payload.email, payload.password, expected_role="admin",
    )
    token = create_access_token(user.id, user.email, user.role)
    return TokenResponse(
        access_token=token, role=user.role,
        full_name=user.full_name, email=user.email,
    )


# ── Current user ─────────────────────────────────────────────────────
@router.get("/me", response_model=UserOut)
def me(payload: dict = Depends(get_current_payload), db: DBSession = Depends(get_db)):
    user = auth_service.get_user_by_email(db, payload["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ── Forgot password ──────────────────────────────────────────────────
@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: DBSession = Depends(get_db)):
    user = auth_service.get_user_by_email(db, payload.email)
    # Always return success (don't leak which emails exist)
    if not user:
        return {"message": "If that email exists, a reset link has been sent."}

    reset_token = create_reset_token(user.id, user.email)

    # TODO: wire up real email sending (SMTP/SendGrid/etc).
    # For now the token is logged so you can test the flow locally.
    logger.info("Password reset token for %s: %s", user.email, reset_token)

    return {
        "message": "If that email exists, a reset link has been sent.",
        # remove reset_token from the response once real email sending is added
        "dev_reset_token": reset_token,
    }


# ── Reset password ───────────────────────────────────────────────────
@router.post("/reset-password")
def reset_password_endpoint(payload: ResetPasswordRequest, db: DBSession = Depends(get_db)):
    data = decode_token(payload.token, expected_type="reset")
    user = auth_service.get_user_by_email(db, data["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    auth_service.reset_password(db, user, payload.new_password)
    logger.info("Password reset for %s", user.email)
    return {"message": "Password reset successful. Please log in."}
