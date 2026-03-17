# SecureShare – Secure File Sharing System

A production-ready REST API built with **FastAPI + PostgreSQL + JWT** that lets authenticated users upload, manage, and download files securely.

---

## Project Structure

```
secureshare/
├── app/
│   ├── main.py        ← App entry point, mounts routers, creates DB tables
│   ├── database.py    ← SQLAlchemy engine + session + get_db() dependency
│   ├── models.py      ← ORM models: User and File tables
│   ├── schemas.py     ← Pydantic schemas for request/response validation
│   ├── auth.py        ← bcrypt hashing, JWT creation/decoding, auth dependency
│   └── routes/
│       ├── users.py   ← POST /register, POST /login
│       └── files.py   ← POST /upload, GET /files, GET /download/{id}, DELETE /files/{id}
├── uploads/           ← Uploaded files stored here (git-ignored)
├── requirements.txt
├── render.yaml        ← One-click Render deployment config
└── .env               ← Local secrets (never commit this file)
```

---

## How the System Works

```
Client
  │
  ├─ POST /register  ──► hash password ──► save User in DB
  │
  ├─ POST /login     ──► verify password ──► return JWT
  │
  ├─ POST /upload    ──► [JWT required] ──► save file to disk + metadata to DB
  │
  ├─ GET  /files     ──► [JWT required] ──► return list of user's files
  │
  ├─ GET  /download/{id} ─► [JWT required] ──► ownership check ──► stream file
  │
  └─ DELETE /files/{id}  ─► [JWT required] ──► ownership check ──► delete
```

Every protected route uses `Depends(get_current_user)` which:
1. Reads the `Authorization: Bearer <token>` header
2. Decodes and validates the JWT
3. Fetches the matching User from the DB
4. Injects the User object into the route handler

---

## Local Setup

### Prerequisites
- Python 3.11+
- PostgreSQL running locally

### 1. Clone / create the project
```bash
cd secureshare
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
Edit `.env` and fill in your values:
```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/secureshare
SECRET_KEY=any-long-random-string-here
```

Create the database in PostgreSQL:
```sql
CREATE DATABASE secureshare;
```

### 5. Run the server
```bash
uvicorn app.main:app --reload
```

Tables are created automatically on first startup.

### 6. Explore the API
Open your browser at:
- **http://localhost:8000/docs** – Swagger UI (interactive)
- **http://localhost:8000/redoc** – ReDoc

---

## API Quick Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | ✗ | Create account |
| POST | `/login` | ✗ | Get JWT token |
| POST | `/upload` | ✓ | Upload a file |
| GET | `/files` | ✓ | List your files |
| GET | `/download/{file_id}` | ✓ | Download a file |
| DELETE | `/files/{file_id}` | ✓ | Delete a file |

### Example workflow with curl

```bash
# Register
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"secret123"}'

# Login – copy the access_token from the response
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"secret123"}'

# Upload (replace TOKEN with your JWT)
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@/path/to/yourfile.pdf"

# List files
curl http://localhost:8000/files \
  -H "Authorization: Bearer TOKEN"

# Download file with id=1
curl http://localhost:8000/download/1 \
  -H "Authorization: Bearer TOKEN" \
  --output downloaded.pdf
```

---

## Deploying to Render

1. Push your code to a GitHub repo (add `.env` and `uploads/` to `.gitignore`).
2. Go to [render.com](https://render.com) → **New Web Service** → connect your repo.
3. Render detects `render.yaml` automatically.
4. In the Render dashboard, set the `DATABASE_URL` environment variable (use Render's managed PostgreSQL or an external provider like Supabase).
5. Deploy – Render runs `pip install -r requirements.txt` then starts uvicorn.

---

## Security Notes

| Concern | How it's handled |
|---------|-----------------|
| Password storage | bcrypt via Passlib (salted + slow hash) |
| Auth tokens | Signed JWTs with expiry |
| File access control | Owner check before every download/delete |
| Filename collisions | UUID prefix added to every stored filename |
| Secret management | All secrets in `.env`, never in source code |
