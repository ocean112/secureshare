"""
main.py
-------
Application entry point.

- Creates all database tables on startup (development convenience).
- Mounts the two route modules.
- Exposes a basic health-check endpoint at GET /
- Auto-generates interactive docs at /docs  (Swagger UI)
                                  and /redoc (ReDoc)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.database import engine
from app import models
from app.routes import users, files

# Create all tables (safe – skips tables that already exist)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SecureShare",
    description="Secure file-sharing API with JWT authentication",
    version="1.0.0",
)

# ── CORS (adjust origins for production) ─────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────
app.include_router(users.router)
app.include_router(files.router)


# ── Serve frontend ───────────────────────────
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", tags=["Frontend"])
def serve_frontend():
    index = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"status": "ok", "message": "SecureShare API is running"}
