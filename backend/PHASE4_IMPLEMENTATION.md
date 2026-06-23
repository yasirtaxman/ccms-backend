# CCMS Phase 4: Medical Management System

Phase 4 adds child medical profiles, clinical visits, medications, vaccinations, medical
document storage, medical reports, dashboard statistics, RBAC, and transactional audit
logging without changing any existing API path.

## Files created

- `app/models/medical_profile.py`
- `app/models/medical_visit.py`
- `app/models/medication.py`
- `app/models/vaccination.py`
- `app/models/medical_document.py`
- `app/schemas/medical.py`
- `app/api/v1/medical.py`
- `alembic/versions/d4e82a7c190b_add_medical_management.py`
- `tests/test_medical.py`
- `PHASE4_IMPLEMENTATION.md`

## Files modified

- `app/services/audit.py`: ten medical audit actions and the `MEDICAL` module.
- `app/main.py`: medical router registration.
- `alembic/env.py`: medical model metadata imports.
- `create_tables.py`: medical model imports for the legacy table helper.

## Migration

- Revision: `d4e82a7c190b`
- Previous revision: `a3c91e5d7b20`
- Tables: `medical_profiles`, `medical_visits`, `medications`, `vaccinations`,
  `medical_documents`
- Includes reversible upgrade/downgrade, foreign keys, unique profile enforcement,
  indexes, actor tracking, timestamps, type/status checks, and date-range checks.

Apply or roll back from `backend/`:

```powershell
alembic upgrade head
alembic downgrade a3c91e5d7b20
```

## RBAC

| Capability | Admin | Manager | Data Entry Operator | Viewer |
|---|---:|---:|---:|---:|
| Read medical data, reports, dashboard | Yes | Yes | Yes | Yes |
| Create/update medical records | Yes | Yes | Yes | No |
| Upload medical documents | Yes | Yes | Yes | No |
| Delete medical documents | Yes | No | No | No |

## Audit actions

- `MEDICAL_PROFILE_CREATE`, `MEDICAL_PROFILE_UPDATE`
- `MEDICAL_VISIT_CREATE`, `MEDICAL_VISIT_UPDATE`
- `MEDICATION_CREATE`, `MEDICATION_UPDATE`
- `VACCINATION_CREATE`, `VACCINATION_UPDATE`
- `MEDICAL_DOCUMENT_UPLOAD`, `MEDICAL_DOCUMENT_DELETE`

Every write adds its audit record in the same database transaction. Failed uploads remove
the partially stored file. Document uploads validate child/visit ownership, document type,
filename, and extension before writing under `uploads/<child_code>/medical/`.

## Endpoints added

### Medical profiles

- `POST /children/{child_id}/medical-profile`
- `GET /children/{child_id}/medical-profile`
- `PUT /children/{child_id}/medical-profile`

### Medical visits

- `POST /children/{child_id}/medical-visits`
- `GET /children/{child_id}/medical-visits`
- `GET /medical-visits/{visit_id}`
- `PUT /medical-visits/{visit_id}`

### Medications

- `POST /children/{child_id}/medications`
- `GET /children/{child_id}/medications`
- `PUT /medications/{medication_id}`

### Vaccinations

- `POST /children/{child_id}/vaccinations`
- `GET /children/{child_id}/vaccinations`
- `PUT /vaccinations/{vaccination_id}`

### Medical documents

- `POST /medical-documents/upload`
- `GET /children/{child_id}/medical-documents`
- `DELETE /medical-documents/{document_id}`

### Reports and dashboard

- `GET /reports/medical-profiles`
- `GET /reports/medical-visits`
- `GET /reports/chronic-diseases`
- `GET /reports/special-needs`
- `GET /reports/active-medications`
- `GET /reports/upcoming-vaccinations`
- `GET /dashboard/medical`

These 23 operations appear in Swagger at `/docs` under Medical, Medical Reports, and
Medical Dashboard tags. OAuth2 authorization remains unchanged.

## Commands executed

```powershell
git switch -c phase4-medical-management
pytest -q -p no:cacheprovider tests
python -m compileall -q app alembic tests
alembic upgrade head --sql
alembic downgrade d4e82a7c190b:a3c91e5d7b20 --sql
git diff --check
```

## Test results

```text
13 passed
```

`tests/test_medical.py` covers profile uniqueness and updates, medical visits,
medications, vaccinations, document upload/type validation/deletion, reports, dashboard,
all medical audit actions, Viewer read-only access, Data Entry writes, and Admin-only
document deletion. The complete Phase 1–4 suite passes.

## Verification checklist

- [x] Branch `phase4-medical-management` created.
- [x] Existing API paths unchanged.
- [x] Five medical tables and model files added.
- [x] SQLAlchemy 2.x and Pydantic v2 patterns used.
- [x] One medical profile per child enforced by database constraint.
- [x] Visit, medication, vaccination, and document constraints validated.
- [x] Allowed file types and extensions enforced.
- [x] RBAC applied to every endpoint.
- [x] Every write operation audited.
- [x] Medical reports and dashboard implemented.
- [x] Router and Alembic metadata registered.
- [x] Upgrade and downgrade SQL verified.
- [x] Python compilation passed.
- [x] Full pytest suite passed: 13 tests.
- [x] Changes committed in logical groups.
