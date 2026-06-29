# CCMS Deployment Guide

This guide keeps deployment practical and repeatable for local demo, staging, and production preparation.

## Required services

- Python backend running FastAPI.
- SQL database supported by the configured SQLAlchemy URL.
- Next.js frontend.
- Persistent upload storage for files uploaded through CCMS.

## Backend deployment checklist

```powershell
cd C:\Users\Yasir\Downloads\cms\backend
$env:PYTHONPATH="."
python -m alembic upgrade head
python -m compileall -q app alembic tests
```

Start command for local validation:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Before production:

- Set a strong `SECRET_KEY`.
- Set `DEBUG=false`.
- Use a production database URL.
- Set trusted CORS origins.
- Confirm `UPLOAD_DIR` is backed up.
- Bootstrap or update the administrator account.
- Change the default development administrator password.

## Frontend deployment checklist

```powershell
cd C:\Users\Yasir\Downloads\cms\frontend
npm install
npm run typecheck
npm run build
```

Set:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-ccms-api.example.org
```

For local demo, keep:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Migration command

Always run migrations before starting the deployed backend:

```powershell
cd C:\Users\Yasir\Downloads\cms\backend
$env:PYTHONPATH="."
python -m alembic upgrade head
```

## Health and readiness

Public safe checks:

- `/health`
- `/health/readiness`

Admin operational checks:

- `/system/readiness`
- `/system/info`

## Demo data

Use demo data only in local demo or training databases:

```powershell
cd C:\Users\Yasir\Downloads\cms\backend
$env:PYTHONPATH="."
python .\scripts\seed_demo_data.py
```

The seed script uses fictional records only and is designed to be rerun safely.
