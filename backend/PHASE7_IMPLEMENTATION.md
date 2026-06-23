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

`GET /imports/templates/children.xlsx` downloads a professionally formatted workbook containing four sheets:

1. **Children Import Template** — the blank upload sheet with frozen headers, filters, date formatting, dropdown validation, and color-coded required fields.
2. **Instructions** — the preparation, preview, correction, and commit workflow.
3. **Allowed Values** — permitted values for `gender` and `status`.
4. **Sample Data** — a complete example for `CCMS-0001 / Ali Khan`; copy its format, not its identifiers.

The 22 columns are: `child_id`, `admission_file_no`, `full_name`, `father_name`, `grandfather_name`, `mother_name`, `gender`, `date_of_birth`, `guardian_name`, `guardian_relationship`, `guardian_cnic`, `guardian_mobile`, `current_address`, `permanent_address`, `village_mohallah`, `union_council`, `tehsil`, `district`, `province`, `admission_date`, `reason_for_admission`, and `status`.

Required columns are marked orange and carry an Excel comment: `child_id`, `admission_file_no`, `full_name`, `gender`, `date_of_birth`, `guardian_name`, `guardian_relationship`, `guardian_mobile`, `district`, `province`, `admission_date`, `reason_for_admission`, and `status`. Blue columns are optional. Dates must use `YYYY-MM-DD`; IDs and admission file numbers must be unique.

Preview and commit accept `.xlsx` and `.csv`, enforce 5,000 rows, validate required fields, dates, allowed values, and duplicate `child_id`/`admission_file_no` values within both the file and database. Commit repeats validation and inserts all rows in one transaction; any validation failure prevents the entire insert. The sample data lives on a separate sheet so the main upload sheet remains safe to fill directly.

For Google Sheets: open the sheet, choose **File > Download > Microsoft Excel (.xlsx)** or **Comma-separated values (.csv)**, then upload the downloaded file. Direct Google API synchronization is intentionally outside Phase 7.

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

1. Login as Admin or Manager and authorize Swagger.
2. Call `GET /imports/templates/children.xlsx` and open the downloaded workbook.
3. Verify the four sheets, read **Instructions**, and review **Sample Data**.
4. Enter one or more children in **Children Import Template** without changing its column names.
5. Save the workbook and submit it as multipart field `file` to `POST /imports/children/preview`.
6. Confirm totals and row-numbered errors; correct every error and preview again.
7. Submit the unchanged, valid file to `POST /imports/children/commit`.
8. Confirm `imported_count`, `skipped_count`, `errors`, and `created_child_ids`.
9. Verify the `IMPORT_PREVIEW` and `IMPORT_COMMIT` audit entries.
10. Upload the same file again and confirm database duplicate validation rejects it.
11. Confirm Data Entry Operator can preview but cannot commit, and Viewer cannot access import endpoints.
