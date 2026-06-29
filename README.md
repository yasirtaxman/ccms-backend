# CCMS – Child Care Management System

CCMS is a reusable child care management platform for orphanages, child welfare organizations, NGOs, child protection institutions, shelter homes, and foster care organizations.

## Local development

Open two PowerShell terminals.

Backend:

```powershell
cd C:\Users\Yasir\Downloads\cms\backend
$env:PYTHONPATH="."
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd C:\Users\Yasir\Downloads\cms\frontend
npm install
npm run dev
```

Frontend must use:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Development login

- Username: `admin`
- Password: `Admin123`
- Backend URL: `http://127.0.0.1:8000`

These credentials are for local development only. Change the default administrator password before training users, staging, or production deployment.

## Demo data

Seed fictional local demo data:

```powershell
cd C:\Users\Yasir\Downloads\cms\backend
$env:PYTHONPATH="."
python .\scripts\seed_demo_data.py
```

Demo users created by the seed script use password `DemoUser123!` and are marked for password change.

## Health checks

- `GET http://127.0.0.1:8000/health`
- `GET http://127.0.0.1:8000/health/readiness`
- Admin-only: `GET http://127.0.0.1:8000/system/readiness`

## Validation commands

Backend:

```powershell
cd C:\Users\Yasir\Downloads\cms\backend
$env:PYTHONPATH="."
python -m alembic upgrade head
python -m pytest tests -q -p no:cacheprovider
python -m compileall -q app alembic tests
```

Frontend:

```powershell
cd C:\Users\Yasir\Downloads\cms\frontend
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
npm run typecheck
npm run build
```

See `DEPLOYMENT.md`, `ENVIRONMENT.md`, `docs\USER_MANUAL.md`, `docs\ADMIN_MANUAL.md`, and `docs\BACKUP_RESTORE.md` for operator guidance.
