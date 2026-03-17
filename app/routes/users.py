"""
routes/users.py
---------------
POST /register          - create account + send verification email
POST /login             - verify credentials, return JWT
GET  /verify-email      - verify email token
POST /forgot-password   - send reset email
POST /reset-password    - set new password with token
GET  /me                - get current user info
"""

import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas, auth
from app.database import get_db
from app.email_service import send_verification_email, send_password_reset_email

router = APIRouter(tags=["Authentication"])


@router.post("/register", response_model=schemas.UserResponse, status_code=201)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email is already registered")

    verify_token = secrets.token_urlsafe(32)
    new_user = models.User(
        email=user_data.email,
        password_hash=auth.hash_password(user_data.password),
        verify_token=verify_token,
        is_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Send verification email (skips silently if SMTP not configured)
    send_verification_email(new_user.email, verify_token)

    return new_user


@router.get("/verify-email", status_code=200)
def verify_email(token: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.verify_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    user.is_verified   = True
    user.verify_token  = None
    db.commit()
    return {"message": "Email verified successfully! You can now log in."}


@router.post("/login", response_model=schemas.Token)
def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not auth.verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = auth.create_access_token(data={"sub": str(user.user_id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/forgot-password", status_code=200)
def forgot_password(payload: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    # Always return success to prevent email enumeration
    if user:
        reset_token = secrets.token_urlsafe(32)
        user.reset_token        = reset_token
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        send_password_reset_email(user.email, reset_token)
    return {"message": "If that email exists, a reset link has been sent."}


@router.post("/reset-password", status_code=200)
def reset_password(payload: schemas.PasswordResetConfirm, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.reset_token == payload.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    if user.reset_token_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token has expired")
    user.password_hash      = auth.hash_password(payload.new_password)
    user.reset_token        = None
    user.reset_token_expiry = None
    db.commit()
    return {"message": "Password reset successfully. You can now log in."}


@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user
