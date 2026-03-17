"""
models.py
---------
Database tables:
  - User      : credentials, email verification, password reset
  - File      : metadata, encryption, file size, share tokens
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id            = Column(Integer, primary_key=True, index=True)
    email              = Column(String, unique=True, index=True, nullable=False)
    password_hash      = Column(String, nullable=False)
    is_verified        = Column(Boolean, default=False)
    verify_token       = Column(String, nullable=True)
    reset_token        = Column(String, nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)
    created_at         = Column(DateTime, default=datetime.utcnow)

    files = relationship("File", back_populates="owner", cascade="all, delete")


class File(Base):
    __tablename__ = "files"

    file_id      = Column(Integer, primary_key=True, index=True)
    filename     = Column(String, nullable=False)
    filepath     = Column(String, nullable=False)
    file_size    = Column(Integer, default=0)
    is_encrypted = Column(Boolean, default=True)
    share_token  = Column(String, nullable=True, index=True)
    owner_id     = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    uploaded_at  = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="files")
