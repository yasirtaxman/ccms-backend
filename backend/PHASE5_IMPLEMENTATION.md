# CCMS Phase 5: Education Management System

Phase 5 tracks each child's complete education history across schools, enrollments, exam
results, monthly attendance, and supporting documents. It adds reports and an academic
dashboard while preserving all existing APIs and Phase 1–4 behavior.

## Files created

- `app/models/school.py`
- `app/models/education_record.py`
- `app/models/exam_result.py`
- `app/models/attendance.py`
- `app/models/education_document.py`
- `app/schemas/education.py`
- `app/api/v1/education.py`
- `alembic/versions/e5f93b8d2a61_add_education_management.py`
- `tests/test_education.py`
- `PHASE5_IMPLEMENTATION.md`

## Files modified

- `app/services/audit.py`: eleven education audit actions and `EDUCATION` module.
- `app/main.py`: education router registration.
- `alembic/env.py`: education model metadata imports.
- `create_tables.py`: education models added to the legacy helper.

## Migration

- Revision: `e5f93b8d2a61`
- Previous revision: `d4e82a7c190b`
- Tables: `schools`, `education_records`, `exam_results`, `attendance`,
  `education_documents`
- Includes complete reversible upgrade/downgrade, indexes, foreign keys, check
  constraints, unique monthly attendance, and a PostgreSQL partial unique index that
  allows only one `Studying` education record per child.

```powershell
alembic upgrade head
alembic downgrade d4e82a7c190b
```

## Business behavior

- A child may retain unlimited historical education records but only one may be
  `Studying` at a time.
- A new active record cannot use an inactive school.
- Child and school ownership are immutable after the education record is created.
- Exam percentage is calculated from obtained and total marks on create and update.
- Attendance percentage is calculated from present and total days on create and update.
- Present plus absent days must equal total days.
- Monthly attendance is unique per education record, month, and year.
- Education records, exam results, and attendance have no delete endpoint.
- Schools can be deleted only by Admin and only when no education history references them.
- Documents are stored under `uploads/<child_code>/education/` and accept PDF/JPG/JPEG/PNG.

## RBAC

| Capability | Admin | Manager | Data Entry Operator | Viewer |
|---|---:|---:|---:|---:|
| Read education data, reports, dashboard | Yes | Yes | Yes | Yes |
| Create/update schools and education data | Yes | Yes | Yes | No |
| Upload education documents | Yes | Yes | Yes | No |
| Delete schools/documents | Yes | No | No | No |

## Audit actions

- `SCHOOL_CREATE`, `SCHOOL_UPDATE`, `SCHOOL_DELETE`
- `EDUCATION_RECORD_CREATE`, `EDUCATION_RECORD_UPDATE`
- `EXAM_RESULT_CREATE`, `EXAM_RESULT_UPDATE`
- `ATTENDANCE_CREATE`, `ATTENDANCE_UPDATE`
- `EDUCATION_DOCUMENT_UPLOAD`, `EDUCATION_DOCUMENT_DELETE`

Every write records an audit event in the same database transaction.

## Endpoints added

### Schools

- `POST /schools`
- `GET /schools`
- `GET /schools/{school_id}`
- `PUT /schools/{school_id}`
- `DELETE /schools/{school_id}`

### Education records

- `POST /children/{child_id}/education-records`
- `GET /children/{child_id}/education-records`
- `GET /education-records/{record_id}`
- `PUT /education-records/{record_id}`

### Exam results

- `POST /education-records/{record_id}/results`
- `GET /education-records/{record_id}/results`
- `PUT /results/{result_id}`

### Attendance

- `POST /education-records/{record_id}/attendance`
- `GET /education-records/{record_id}/attendance`
- `PUT /attendance/{attendance_id}`

### Education documents

- `POST /education-documents/upload`
- `GET /children/{child_id}/education-documents`
- `DELETE /education-documents/{document_id}`

### Reports and dashboard

- `GET /dashboard/education`
- `GET /reports/students`
- `GET /reports/schools`
- `GET /reports/exam-results`
- `GET /reports/top-performers`
- `GET /reports/low-attendance`
- `GET /reports/dropout-students`
- `GET /reports/board-exam-students`

These 26 operations appear in Swagger `/docs` under Education, Education Reports, and
Education Dashboard.

## Test results

```text
16 passed
```

`tests/test_education.py` covers school CRUD, Admin deletion guards, Viewer/Data Entry
RBAC, active-record exclusivity, education history, calculated exam and attendance
percentages, duplicate attendance rejection, every report, dashboard values, file upload
and deletion, and all education audit actions.

## Commands executed

```powershell
git switch -c phase5-education-management
pytest -q -p no:cacheprovider tests
python -m compileall -q app alembic tests
alembic upgrade head --sql
alembic downgrade e5f93b8d2a61:d4e82a7c190b --sql
git diff --check
```

## Verification checklist

- [x] Branch `phase5-education-management` created.
- [x] Five requested model files and tables created.
- [x] Existing API paths unchanged.
- [x] Historical education records cannot be deleted through the API.
- [x] One active education record per child enforced in service and database.
- [x] Exam and attendance percentages automatically calculated.
- [x] Board students, dropouts, top performers, and low attendance reported.
- [x] Academic dashboard implemented.
- [x] Upload type, extension, and child-record ownership validated.
- [x] RBAC applied to every endpoint.
- [x] Every write audited.
- [x] Migration upgrade and downgrade SQL verified.
- [x] Python compilation passed.
- [x] Full Phase 1–5 test suite passed: 16 tests.
