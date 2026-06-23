# CCMS Phase 2: Sponsor Management

Phase 2 adds sponsor records, historical child sponsorships, search, reports, RBAC,
actor tracking, transactional audit logging, validation, migrations, and tests.

## Access policy

| Capability | Admin | Manager | Data Entry Operator | Viewer |
|---|---:|---:|---:|---:|
| Create/update/view sponsors | Yes | Yes | Yes | View only, sensitive fields masked |
| Deactivate sponsors | Yes | No | No | No |
| Create/update/view sponsorships | Yes | Yes | Yes | View only |
| View sponsor reports | Yes | Yes | Yes | Yes |

`DELETE /sponsors/{id}` sets `deleted_at` and `deleted_by`, records a `DELETE` audit
event, and retains both the sponsor and every sponsorship. Deleted sponsors are excluded
from normal lookup, search, list, and report endpoints. Their business status is not
repurposed. Sponsorships have no delete endpoint.

Viewer responses omit CNIC/passport, email, mobile numbers, and the full address. Viewers
also cannot search by email or mobile. Admin, Manager, and Data Entry Operator responses
retain the complete sponsor schema.

All sponsor and sponsorship rows store `created_by`, `updated_by`, `created_at`, and
`updated_at`. Both tables now include nullable, indexed `organization_id` placeholders;
no tenant filtering or multi-tenancy behavior is enabled. Sponsor deletion adds
`deleted_at` and `deleted_by`.

`sponsor_id` is immutable after sponsorship creation in both the update schema and a
PostgreSQL trigger. Overlapping periods for the same child/sponsor pair are rejected by
the service and a PostgreSQL GiST exclusion constraint. Status changes emit the dedicated
`SPONSORSHIP_STATUS_CHANGE` audit action. Audit payload columns use PostgreSQL JSONB,
while the SQLAlchemy type retains a JSON fallback for test databases.

## Files created

- `app/models/sponsor.py`
- `app/schemas/sponsor.py`
- `app/api/v1/sponsors.py`
- `alembic/versions/e31a8d2f6b47_add_sponsor_management.py`
- `alembic/versions/f84c0d9a217e_harden_sponsor_management.py`
- `tests/test_sponsors.py`
- `PHASE2_IMPLEMENTATION.md`

## Files modified

- `app/models/child.py`: Child-to-sponsorship relationship.
- `app/core/deps.py`: Data Entry-enabled sponsor read policy.
- `app/services/audit.py`: `SPONSORS` and `SPONSORSHIPS` modules.
- `app/main.py`: Sponsor router registration.
- `alembic/env.py` and `create_tables.py`: Sponsor model metadata imports.

## Migration and startup

From `backend/`:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Rollback only Phase 2:

```powershell
alembic downgrade 7c13f21a934e
```

## API test sequence

1. Log in through `/auth/login` or authorize through Swagger `/docs`.
2. Create a sponsor with `POST /sponsors`.
3. Search using `GET /sponsors/search?name=Ayesha&status=Active`.
4. Update it with `PUT /sponsors/{id}`.
5. Create history with `POST /children/{child_id}/sponsorships`.
6. Read both perspectives using `GET /children/{child_id}/sponsorships` and
   `GET /sponsors/{sponsor_id}/children`.
7. Complete or suspend it with `PUT /sponsorships/{id}`.
8. Call the four `/reports/...` endpoints.
9. As Admin, deactivate the sponsor with `DELETE /sponsors/{id}`.
10. Confirm Viewer responses omit all protected contact and identity fields.
11. Confirm overlapping periods return `409` and `sponsor_id` updates return `422`.
12. Confirm `GET /audit-logs` contains `SPONSORSHIP_STATUS_CHANGE` events.

## Tests

```powershell
pip install pytest httpx
pytest -q
pytest -q tests/test_sponsors.py
python -m compileall -q app alembic scripts tests
```
