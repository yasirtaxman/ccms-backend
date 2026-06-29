# CCMS Admin Manual

This guide is for administrators responsible for setup, access control, demo preparation, backup, and troubleshooting.

## 1. User management

Use Administration → Users to create staff accounts, activate or deactivate users, assign roles, and reset passwords.

## 2. Roles and permissions

Use Roles & Permission Matrix to review module permissions. Admin has full access. Be careful when granting export, import commit, audit, or sensitive development permissions.

## 3. Organization profile

Maintain the organization profile before generating reports so exported PDFs show the correct name, address, footer, watermark, and signatory information.

## 4. Audit trail

Use Audit Logs to review security and operational events. Audit logs should be treated as administrative records.

## 5. Demo data

Run fictional demo data only in a local demo database:

```powershell
cd C:\Users\Yasir\Downloads\cms\backend
$env:PYTHONPATH="."
python .\scripts\seed_demo_data.py
```

Seeded users:

- `demo_admin`
- `demo_manager`
- `demo_warden`
- `demo_viewer`

Password:

```text
DemoUser123!
```

Demo users are marked for password change.

## 6. Backup and restore

Follow `docs\BACKUP_RESTORE.md`. Back up both the database and upload folder.

## 7. Deployment commands

Backend:

```powershell
cd C:\Users\Yasir\Downloads\cms\backend
$env:PYTHONPATH="."
python -m alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd C:\Users\Yasir\Downloads\cms\frontend
npm run typecheck
npm run build
npm run start
```

## 8. Change default admin password

The local development administrator may use `Admin123`. Change it before staff training, staging, or production. Use the Change Password menu or an approved administrative reset workflow.

## 9. Troubleshooting

- Backend not reachable: confirm `http://127.0.0.1:8000/health`.
- Frontend login fails: confirm `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`.
- Database errors: run `python -m alembic current` and `python -m alembic upgrade head`.
- Exports fail: confirm `openpyxl` and `reportlab` are installed.
- Upload issues: confirm `UPLOAD_DIR` exists and the backend process can write to it.
- Permission issue: review the user’s assigned roles and role permissions.
