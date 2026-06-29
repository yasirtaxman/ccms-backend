# CCMS Backup and Restore Guide

Back up both the database and uploaded files. A database backup without uploads may leave document records pointing to missing files.

## SQLite local backup

If `DATABASE_URL` points to a local SQLite file, stop the backend first, then copy the database file:

```powershell
Copy-Item C:\path\to\ccms.db C:\path\to\backups\ccms-$(Get-Date -Format yyyyMMdd-HHmm).db
```

Restore by stopping the backend and copying the selected backup over the active database file.

## PostgreSQL backup

Backup:

```powershell
pg_dump -Fc -f C:\backups\ccms-$(Get-Date -Format yyyyMMdd-HHmm).dump ccms
```

Restore to an empty database:

```powershell
pg_restore --clean --if-exists -d ccms C:\backups\ccms-YYYYMMDD-HHMM.dump
```

Run migrations after restore:

```powershell
cd C:\Users\Yasir\Downloads\cms\backend
$env:PYTHONPATH="."
python -m alembic upgrade head
```

## Upload backup

Back up the configured `UPLOAD_DIR` folder:

```powershell
Compress-Archive -Path C:\Users\Yasir\Downloads\cms\backend\uploads -DestinationPath C:\backups\ccms-uploads-$(Get-Date -Format yyyyMMdd-HHmm).zip
```

Restore uploads before staff use the system so document download links remain valid.

## Recommended schedule

- Local demo: before and after major demos.
- Staging: daily while testing.
- Production: daily database backup, daily upload backup, and a weekly off-server copy.

## Restore cautions

- Restore into a test environment first when possible.
- Confirm application version and migration level.
- Keep the old backup until staff confirm the restored system is working.
- Never restore demo data into a production database.
