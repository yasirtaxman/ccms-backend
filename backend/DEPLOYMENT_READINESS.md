# CCMS Deployment Readiness

## Configuration

Copy `.env.example` to `.env` and replace every sample secret. Required production values include `DATABASE_URL`, a long random `SECRET_KEY`, `ENVIRONMENT=production`, explicit `BACKEND_CORS_ORIGINS`, `ALLOWED_HOSTS`, `UPLOAD_DIR`, and `ADMIN_USERNAME`/`ADMIN_PASSWORD` for initial bootstrap. Never commit `.env`.

Install and run locally:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH="."
python -m alembic upgrade head
uvicorn app.main:app --reload
```

Production should use PostgreSQL and a supervised ASGI process, for example `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`. Run `python -m alembic upgrade head` once during deployment.

Create the upload directory with write access limited to the service account. Configure only trusted frontend origins and public hostnames. Bootstrap canonical roles and the first Admin with:

```powershell
$env:ADMIN_USERNAME="system-admin"
$env:ADMIN_PASSWORD="a-strong-unique-password"
python scripts/bootstrap_admin.py
```

Production bootstrap fails if the password is absent. Development fallback emits a warning and forces password change.

Passwords require 8+ characters with uppercase, lowercase, number, and special character; they cannot contain the username or be a common password. Back up PostgreSQL and the upload directory together, encrypt backups, restrict retention access, and test restore procedures.

Smoke test `/health`, Admin login, `/system/readiness`, `/system/info`, user creation/deactivation, dashboards, import template, one safe preview, exports, `/docs`, CORS, host filtering, security headers, request IDs, and audit events.
