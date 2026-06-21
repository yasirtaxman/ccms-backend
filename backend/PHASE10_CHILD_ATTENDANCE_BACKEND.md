# CCMS Phase 10 — Daily Child Attendance Backend

## Implementation

Created the `DailyChildAttendance` model, strict Pydantic schemas, service helpers, API router, Alembic migration `c10a7d4e2b91`, and automated tests. Modified application router registration, audit enums, dashboard alerts, Children/document read RBAC, Alembic metadata imports, and the API contract.

Created files:

- `app/models/child_attendance.py`
- `app/schemas/child_attendance.py`
- `app/services/child_attendance_service.py`
- `app/api/v1/child_attendance.py`
- `alembic/versions/c10a7d4e2b91_add_daily_child_attendance.py`
- `tests/test_child_attendance.py`

Modified files: `app/main.py`, `app/services/audit.py`, `app/services/dashboard_service.py`, `app/api/v1/children.py`, `app/api/v1/documents.py`, `alembic/env.py`, and `API_CONTRACT.md`.

The `daily_child_attendance` table stores one active record per child/date using a partial unique index. It supports nine presence statuses, optional check-in/out times and remarks, full create/update/delete attribution, and soft deletion. Check-out cannot precede check-in.

## Endpoints

- `POST/GET /children/{child_id}/daily-attendance`
- `GET /daily-attendance` with date/range/status/child pagination
- `PUT/DELETE /daily-attendance/{attendance_id}`
- `POST /daily-attendance/bulk-mark`
- `GET /daily-attendance/today`
- `GET /reports/daily-attendance`
- `GET /reports/monthly-child-attendance`
- `GET /dashboard/daily-attendance`

Bulk marking validates all children and duplicate request rows before changing data, then creates or updates all records in one transaction. Missing and Unauthorized Absence are exposed in `/dashboard/alerts`.

## RBAC and audit

Admin has full access; Manager and Data Entry Operator can create/update/bulk mark; Viewer is read-only; delete is Admin-only. Audit module `DAILY_ATTENDANCE` records create, update, delete, and bulk-mark actions without sensitive payloads.

## Validation

```powershell
$env:PYTHONPATH="."
python -m alembic upgrade head
python -m pytest tests -q -p no:cacheprovider
python -m compileall -q app alembic tests
```

## Manual checklist

1. Start backend from `C:\Users\Yasir\Downloads\cms\backend` with the virtual environment, `PYTHONPATH=.`, and `uvicorn app.main:app --reload`.
2. Start frontend from `C:\Users\Yasir\Downloads\cms\frontend` with `npm run dev`.
3. Open `http://localhost:3000/login` and sign in as `admin` / `Admin123`.
4. Open `/dashboard/children`; load, create, view, and edit a child.
5. Download Children Excel/PDF and a full child profile.
6. Download the import template, preview a file, then commit a valid import.
7. Open `/dashboard/children/attendance`, select today, mark all Present, and save.
8. Change one child to Medical Leave and save again.
9. Open attendance reports and run the monthly summary.
10. Sign in as Viewer and confirm read-only Children/attendance access with no create, edit, import, mark, verify, or delete controls.
