# CCMS Phase 3: Accommodation Management

Phase 3 adds the complete Building → Block → Floor → Room → Bed hierarchy, historical
bed allocations, transfers, vacations, reports, dashboard statistics, RBAC, auditing,
soft deletion, future organization placeholders, and database-enforced occupancy rules.

## Design and business rules

- All hierarchy tables include nullable `organization_id`, actor/timestamp tracking,
  `deleted_at`, and `deleted_by`.
- Bed allocations are never deleted and retain the complete child/bed history.
- PostgreSQL partial unique indexes permit only one `Active` allocation per child and bed.
- Allocation and transfer lock the child and accommodation rows before changing state.
- Allocation changes the bed to `Occupied`; transfer/vacation releases the previous bed.
- Only `Vacant` beds under active, non-deleted rooms, floors, blocks, and buildings can
  receive allocations. Reserved and Maintenance beds are unavailable.
- Room rows are locked during bed creation, and bed count cannot exceed room capacity.
- A room capacity cannot be reduced below its existing non-deleted bed count.
- Parents cannot be deleted if any child row exists, including soft-deleted history.
- Structural deletion and allocation workflows write audit events in the same transaction.

## RBAC

| Capability | Admin | Manager | Data Entry Operator | Viewer |
|---|---:|---:|---:|---:|
| View hierarchy, allocations, reports, dashboard | Yes | Yes | Yes | Yes |
| Create/update hierarchy and allocations | Yes | Yes | Yes | No |
| Transfer/vacate beds | Yes | Yes | Yes | No |
| Soft-delete hierarchy records | Yes | No | No | No |

## Files created

- `app/models/accommodation.py`
- `app/schemas/accommodation.py`
- `app/api/v1/accommodation.py`
- `alembic/versions/a3c91e5d7b20_add_accommodation_management.py`
- `tests/test_accommodation.py`
- `PHASE3_IMPLEMENTATION.md`

## Files modified

- `app/core/deps.py`: operational read policy for Data Entry and Viewer access.
- `app/services/audit.py`: accommodation modules and allocation workflow actions.
- `app/main.py`: accommodation router registration.
- `alembic/env.py` and `create_tables.py`: accommodation metadata imports.

## Database migration

Revision: `a3c91e5d7b20`, following `f84c0d9a217e`.

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

Rollback Phase 3:

```powershell
alembic downgrade f84c0d9a217e
```

## API test sequence

1. Create Building, Block, Floor, Room, and Beds in hierarchy order.
2. Create a bed allocation with `POST /bed-allocations`.
3. Confirm the bed is `Occupied` and duplicate child/bed allocations return `409`.
4. Transfer using `POST /bed-allocations/{id}/transfer` and confirm both history rows.
5. Vacate the replacement using `POST /bed-allocations/{id}/vacate`.
6. Confirm the bed returns to `Vacant` and history remains available.
7. Call the twelve accommodation report endpoints and `/dashboard/accommodation`.
8. Confirm Viewer is read-only and structural deletion is Admin-only.
9. Confirm `GET /audit-logs` includes create/update/delete, `BED_ALLOCATION`,
   `BED_TRANSFER`, and `BED_VACATION` records.

## Verification commands

```powershell
pip install pytest httpx
pytest -q
pytest -q tests/test_accommodation.py
python -m compileall -q app alembic scripts tests
alembic upgrade f84c0d9a217e:a3c91e5d7b20 --sql
alembic downgrade a3c91e5d7b20:f84c0d9a217e --sql
```
