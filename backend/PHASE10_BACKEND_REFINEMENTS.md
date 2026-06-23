# CCMS Phase 10 - Backend Refinements

## Admission document workflow

- `GET /documents/admission-document-types` returns the approved required/optional dropdown definitions and extensions.
- `GET /children/{child_id}/documents/checklist` returns required, uploaded, verified, count, latest-document, and status fields.
- The existing upload route validates approved types and extensions. Legacy Phase 1 document names remain accepted for backward compatibility.
- `GET /children/{child_id}/admission-checklist` remains available and retains its original keys while also returning the structured checklist.

Required types are Admission Form, Child Photo, Birth Certificate / Form-B, Guardian CNIC, Father Death Certificate, and Medical Certificate. Optional types are School / Education Record, Court / Legal Order, and Other Supporting Document.

## Attendance and exports

Daily attendance list, today, and report responses now include active building, block, floor, room, and bed information. Monthly rows include gender and district. New endpoints are:

- `GET /exports/daily-attendance.pdf`
- `GET /exports/monthly-child-attendance.pdf`
- `GET /exports/daily-attendance.xlsx`
- `GET /exports/monthly-child-attendance.xlsx`

PDF reports use a CCMS header, selected period, generated-by metadata, professional landscape table, privacy-safe columns, and page-numbered footer. Export actions are audited.

The full-profile PDF no longer produces duplicate padding text and uses the latest uploaded Child Photo when a valid image file exists. Sponsor contact and identity fields remain excluded.

## Testing

```powershell
$env:PYTHONPATH="."
python -m alembic upgrade head
python -m pytest tests -q -p no:cacheprovider
python -m compileall -q app alembic tests
```

No schema migration is required for these response, validation, report, and frontend integration refinements.
