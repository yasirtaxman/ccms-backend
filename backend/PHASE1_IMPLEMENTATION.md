# CCMS Phase 1: Security, RBAC, Authorization and Audit Trail

This implementation adds authenticated current-user resolution, OAuth2 bearer support,
role-based route protection, admin role-management APIs, and transactional audit logs.

## Role policy

| Capability | Admin | Manager | Data Entry Operator | Viewer |
|---|---:|---:|---:|---:|
| Create/update children and upload/verify documents | Yes | Yes | Yes | No |
| Read children, documents and checklists | Yes | Yes | No | Yes |
| Delete documents | Yes | No | No | No |
| Manage roles and read audit logs | Yes | No | No | No |

Admin is always accepted by every protected dependency. Authentication endpoints remain
public. `/auth/login` preserves the existing JSON contract; `/auth/token` is the OAuth2
form endpoint used by Swagger.

## Installation and migration

From `backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

For an existing database, register the first administrator, then run the one-time,
idempotent bootstrap command. It creates the four canonical roles and assigns Admin:

```powershell
python scripts/bootstrap_admin.py admin
```

The structural migration is fully reversible with `alembic downgrade -1`.

## Verification sequence

1. Register a user with `POST /auth/register`.
2. Bootstrap that username once using the command above.
3. Log in through `POST /auth/login`, or open `/docs`, click **Authorize**, and enter
   the username/password (Swagger calls `/auth/token`).
4. Call `GET /auth/me` and confirm identity and roles.
5. As Admin, create a role with `POST /roles` and assign it with
   `POST /users/{user_id}/roles/{role_id}`.
6. Confirm Viewer can call `GET /children` but receives 403 for `POST /children`.
7. As Admin, call `GET /audit-logs` and confirm registration, login, child, document,
   and role events.

Run the automated security suite from `backend/`:

```powershell
pip install pytest httpx
pytest -q
```

## Files

Created: `app/models/audit_log.py`, `app/schemas/audit.py`, `app/schemas/role.py`,
`app/services/audit.py`, `app/api/v1/roles.py`, `app/api/v1/audit_logs.py`, the Phase 1
Alembic revision, bootstrap script, tests, and this guide.

Modified: authentication, child and document routers; user/role models and user schemas;
dependency wiring; application router registration; Alembic metadata imports; and the
legacy table-creation helper.
