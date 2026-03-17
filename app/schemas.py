"""
schemas.py — Pydantic request/response models
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    email:    EmailStr
    password: str

class UserResponse(BaseModel):
    user_id:     int
    email:       str
    is_verified: bool
    created_at:  datetime
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email:    EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token:        str
    new_password: str

class FileResponse(BaseModel):
    file_id:      int
    filename:     str
    file_size:    int
    is_encrypted: bool
    share_token:  Optional[str]
    uploaded_at:  datetime
    class Config:
        from_attributes = True

class ShareResponse(BaseModel):
    share_url: str
    token:     str
