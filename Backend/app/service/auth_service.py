"""
app/service/auth_service.py — Business logic for registration, login, password reset.
"""

from sqlalchemy.orm import Session as DBSession
from fastapi import HTTPException, status

from app.models import User
from app.utils.security import hash_password, verify_password


def get_user_by_email(db: DBSession, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(db: DBSession, full_name: str, email: str, password: str,
                 university: str | None = None, role: str = "student") -> User:
    if get_user_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user = User(
        full_name=full_name,
        email=email,
        hashed_password=hash_password(password),
        university=university,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: DBSession, email: str, password: str,
                       expected_role: str | None = None) -> User:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled",
        )
    if expected_role and user.role != expected_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This login is for {expected_role} accounts only",
        )
    return user


def reset_password(db: DBSession, user: User, new_password: str) -> None:
    user.hashed_password = hash_password(new_password)
    db.commit()
