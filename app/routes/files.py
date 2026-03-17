"""
routes/files.py
---------------
POST   /upload                - upload + encrypt file
GET    /files                 - list user files (supports ?search=)
GET    /download/{file_id}    - download + decrypt (owner only)
DELETE /files/{file_id}       - delete file (owner only)
POST   /files/{file_id}/share - generate shareable link
DELETE /files/{file_id}/share - revoke shareable link
GET    /shared/{token}        - public download via share token
"""

import os
import uuid
import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app import models, schemas, auth
from app.database import get_db
from app.encryption import encrypt_file, decrypt_file

load_dotenv()

router    = APIRouter(tags=["Files"])
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
BASE_URL  = os.getenv("BASE_URL", "http://localhost:8000")


def _get_owned_file(file_id: int, current_user: models.User, db: Session) -> models.File:
    file = db.query(models.File).filter(models.File.file_id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if file.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return file


def _format_size(size: int) -> str:
    for unit in ['B','KB','MB','GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


# ── Upload ────────────────────────────────────
@router.post("/upload", response_model=schemas.FileResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    content = await file.read()
    original_size = len(content)

    # Encrypt before saving to disk
    encrypted = encrypt_file(content)

    unique_prefix = uuid.uuid4().hex[:8]
    safe_filename = f"{unique_prefix}_{file.filename}.enc"
    file_path = UPLOAD_DIR / safe_filename

    with open(file_path, "wb") as f:
        f.write(encrypted)

    db_file = models.File(
        filename=file.filename,
        filepath=str(file_path),
        file_size=original_size,
        is_encrypted=True,
        owner_id=current_user.user_id,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


# ── List files ────────────────────────────────
@router.get("/files", response_model=list[schemas.FileResponse])
def list_files(
    search: str = Query(default="", description="Search by filename"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.File).filter(models.File.owner_id == current_user.user_id)
    if search:
        query = query.filter(models.File.filename.ilike(f"%{search}%"))
    return query.order_by(models.File.uploaded_at.desc()).all()


# ── Download ──────────────────────────────────
@router.get("/download/{file_id}")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    db_file = _get_owned_file(file_id, current_user, db)
    if not os.path.exists(db_file.filepath):
        raise HTTPException(status_code=404, detail="File not found on server")

    with open(db_file.filepath, "rb") as f:
        data = f.read()

    decrypted = decrypt_file(data) if db_file.is_encrypted else data
    return Response(
        content=decrypted,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{db_file.filename}"'}
    )


# ── Delete ────────────────────────────────────
@router.delete("/files/{file_id}", status_code=204)
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    db_file = _get_owned_file(file_id, current_user, db)
    try:
        os.remove(db_file.filepath)
    except FileNotFoundError:
        pass
    db.delete(db_file)
    db.commit()


# ── Share: generate link ──────────────────────
@router.post("/files/{file_id}/share", response_model=schemas.ShareResponse)
def create_share_link(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    db_file = _get_owned_file(file_id, current_user, db)
    if not db_file.share_token:
        db_file.share_token = secrets.token_urlsafe(32)
        db.commit()
        db.refresh(db_file)
    return {"share_url": f"{BASE_URL}/shared/{db_file.share_token}", "token": db_file.share_token}


# ── Share: revoke link ────────────────────────
@router.delete("/files/{file_id}/share", status_code=204)
def revoke_share_link(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    db_file = _get_owned_file(file_id, current_user, db)
    db_file.share_token = None
    db.commit()


# ── Public shared download ────────────────────
@router.get("/shared/{token}")
def download_shared(token: str, db: Session = Depends(get_db)):
    db_file = db.query(models.File).filter(models.File.share_token == token).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="Share link is invalid or has been revoked")
    if not os.path.exists(db_file.filepath):
        raise HTTPException(status_code=404, detail="File not found on server")

    with open(db_file.filepath, "rb") as f:
        data = f.read()

    decrypted = decrypt_file(data) if db_file.is_encrypted else data
    return Response(
        content=decrypted,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{db_file.filename}"'}
    )
