# CCMS Phase 7 Implementation

Phase 7 adds consolidated dashboards, reports, safe search/profile summaries, in-memory Excel/PDF exports, and transactional Excel/CSV child imports. No database schema change is required; therefore no Alembic revision was added.

## Files created

- `app/api/v1/dashboard.py`
- `app/api/v1/consolidated_reports.py`
- `app/api/v1/exports.py`
- `app/api/v1/imports.py`
- `app/schemas/dashboard.py`
- `app/schemas/consolidated_reports.py`
- `app/schemas/import_export.py`
- `app/services/dashboard_service.py`
- `app/services/report_service.py`
- `app/services/excel_service.py`
- `app/services/pdf_service.py`
- `app/services/import_service.py`
- `PHASE7_IMPLEMENTATION.md`

## Files modified

- `app/main.py`: registers dashboard, consolidated-report, export, and import routers.
- `app/services/audit.py`: adds `IMPORT_EXPORT`, `EXPORT_EXCEL`, `EXPORT_PDF`, `IMPORT_PREVIEW`, and `IMPORT_COMMIT`.
- `requirements.txt`: adds `openpyxl==3.1.5` and `reportlab==4.4.2`.

## APIs

Dashboards and search:

- `GET /dashboard/executive`
- `GET /dashboard/operational`
- `GET /dashboard/alerts`
- `GET /children/{child_id}/complete-profile-summary`
- `GET /search/global?q=ali`

Reports:

- `GET /reports/consolidated/children`
- `GET /reports/consolidated/sponsorships`
- `GET /reports/consolidated/accommodation`
- `GET /reports/consolidated/medical`
- `GET /reports/consolidated/education`
- `GET /reports/consolidated/case-management`
- `GET /reports/audit-summary` (Admin only)

Excel exports:

- `/exports/children.xlsx`, `/exports/sponsors.xlsx`, `/exports/sponsorships.xlsx`
- `/exports/accommodation.xlsx`, `/exports/medical.xlsx`, `/exports/education.xlsx`
- `/exports/case-management.xlsx`, `/exports/full-child-profile/{child_id}.xlsx`

PDF exports:

- `/exports/children.pdf`, `/exports/sponsors.pdf`, `/exports/accommodation.pdf`
- `/exports/medical.pdf`, `/exports/education.pdf`, `/exports/case-management.pdf`
- `/exports/full-child-profile/{child_id}.pdf`

Imports:

- `GET /imports/templates/children.xlsx`
- `POST /imports/children/preview`
- `POST /imports/children/commit`

## Import format and workflow

The template contains the 22 Child fields, a sample row, instructions, allowed gender/status values, and the required `YYYY-MM-DD` date format. Preview and commit accept `.xlsx` and `.csv`, enforce 5,000 rows, validate every required field, and detect duplicate `child_id` and `admission_file_no` values both within the file and database. Commit revalidates and uses one transaction.

For Google Sheets: open the sheet, choose **File > Download**, select Microsoft Excel or CSV, then upload the downloaded file. Direct Google API synchronization is intentionally outside Phase 7.

## RBAC and masking

- Admin: all functionality, including audit summary and import commit.
- Manager: operational access, exports, import preview/commit.
- Data Entry Operator: operational access, safe exports, import preview only.
- Viewer: read-only dashboards/reports and safe exports; alert references are reduced to counts; imports and audit summary are denied.
- Dashboard/report/export projections omit guardian and sponsor identification numbers, full addresses, case notes, medical diagnoses, and treatment notes.

## Audit

Exports record report type and filters. Preview records filename and validation totals. Commit records filename, imported count, user ID, and created child IDs. Imports use one summary event rather than one event per child.

## Validation commands

```powershell
python -m pytest tests -q -p no:cacheprovider
python -m compileall -q app alembic tests
python -m alembic current
python -m alembic upgrade head
```

## Swagger verification checklist

1. Login as Admin and authorize Swagger.
2. Call executive, operational, and alerts dashboards.
3. Call the complete child profile and global search.
4. Call all six consolidated reports and confirm pagination/filter metadata.
5. Download children and full-profile Excel/PDF exports.
6. Download the child import template.
7. Preview a valid import, then commit it.
8. Verify export/import events in audit logs.
9. Login as Viewer; confirm alert references and sensitive fields are absent.
10. Confirm Viewer imports and audit summary are denied.

## Manual API import test

Download the template, delete its sample row, enter one or more unique children, and save it. Submit it as multipart form field `file` to preview. Resolve every row-numbered error, repeat preview, then submit the unchanged file to commit. Reusing it must be rejected as duplicate data.
