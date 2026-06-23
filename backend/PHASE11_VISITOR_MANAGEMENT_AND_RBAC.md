# Phase 11: Visitor Management and Detailed RBAC

## Overview

Phase 11 adds verified visitor records, supervised child meetings, operational reports, Excel/PDF exports, audit events, a detailed permission catalogue, and the Warden system role. Visitor identity and contact fields are returned only to authorized operational roles; general reports omit CNIC/passport and mobile values.

## Workflows

1. Create a visitor in `Pending Verification` state.
2. Verify the visitor with `POST /visitors/{id}/verify`; verification records the method, user, and time.
3. Schedule a meeting with one child and one non-blocked visitor.
4. Admin or Manager approves or rejects the request. An unverified visitor requires an Admin override.
5. An approved meeting can be checked in, then checked out. Checkout cannot precede check-in.
6. Cancelling/deleting preserves history through state changes and audit records.

Blocked visitors cannot be scheduled. Completed meetings are protected from ordinary edits. Create, update, verification, approval, rejection, check-in, check-out, cancellation, blocking, and activation actions are audited.

## Permissions and Warden Role

Permissions use `module.action` names and are stored in `permissions` and `role_permissions`. Admin always has full access and its permission set is protected. System roles cannot be deleted. Custom roles can be created, assigned permissions, assigned to users, and deleted when unused.

The Warden role is intended for a future Android client and defaults to dashboard, limited child/accommodation viewing, daily attendance management, approved/pending visit viewing, visit creation, and visit check-in/check-out. It cannot approve visits, export confidential information, or access administrative and confidential case modules. The REST APIs are token-based and contain no browser-only dependency, making them suitable for a later mobile client; no Android application is included in this phase.

## Endpoints Added

- Visitors: `GET/POST /visitors`, `GET/PUT/DELETE /visitors/{id}`, and verify, block, activate actions.
- Meetings: `GET/POST /child-visits`, `GET/PUT/DELETE /child-visits/{id}`, and approve, reject, check-in, check-out, cancel actions.
- Integration: `GET /children/{id}/visits`, `GET /visitors/{id}/visits`.
- Reporting: `/reports/visitors`, `/reports/child-visits`, `/reports/visitors/daily`, `/reports/visitors/monthly`.
- Dashboard: `GET /dashboard/visitors`.
- Exports: visitor and child-visit daily/monthly `.pdf` and `.xlsx` routes under `/exports`.
- RBAC: permission catalogue, role CRUD, role-permission replacement/add/remove, and user-role assignment routes under `/roles`.

## Database Migration

- `b11c4e7a903f_add_visitors_and_detailed_permissions.py`: visitors, child visits, permissions, role mappings, system roles, Warden defaults.
- `c11d8f2b704a_track_role_permission_configuration.py`: records whether a role's explicit permission set has been configured, including an intentionally empty set.

## Testing

```powershell
cd C:\Users\Yasir\Downloads\cms\backend
$env:PYTHONPATH="."
.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m compileall -q app alembic tests
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Manual test: log in as `admin`, create and verify a visitor, schedule and approve a meeting, check it in/out, inspect visitor reports/exports and audit logs, edit Warden permissions on the Roles page, then confirm a Warden sees only permitted navigation/actions and Viewer remains read-only.

## Known Limitations

- No Android client is included.
- Visitor photographs use the optional path field; no new binary upload subsystem was introduced.
- Organization/multi-tenant partitioning is outside this phase.
