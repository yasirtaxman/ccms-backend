# CCMS Phase 10 - Exports and Safe Actions

## Export updates

The shared PDF report builder now produces professional CCMS reports with:

- A4 portrait by default and landscape for wide tables;
- branded CCMS header and human-readable report title;
- generated-by, generated-at, and readable filter metadata;
- total and applicable status summary cards;
- numbered rows, human-friendly column labels, alternating rows, repeated table headers, and readable borders;
- professional empty state and a system-generated page footer;
- removal of credential, identity-document, contact, address, detailed medical, and restricted fields.

Sponsorship PDF export is now available at `GET /exports/sponsorships.pdf`. Safe Admin-only user and audit exports are available at:

- `GET /exports/users.pdf`
- `GET /exports/users.xlsx`
- `GET /exports/audit-summary.pdf`
- `GET /exports/audit-summary.xlsx`

The user report never includes password hashes or tokens. Audit summary exports omit JSON payloads. Sponsor reports continue to omit mobile numbers, alternate mobile numbers, CNIC/passport, and full address.

## Existing safe actions used by the frontend

The frontend calls existing guarded endpoints for sponsor soft deletion, accommodation dependency-aware deletion, bed transfer/vacation, school deletion, case soft deletion and lifecycle transitions, and user activation/deactivation/password reset/role assignment. No backend business rule was weakened and no child hard delete was introduced. Destructive operations remain protected by backend RBAC and dependency checks.

## Testing

```powershell
$env:PYTHONPATH="."
python -m pytest tests -q -p no:cacheprovider
python -m compileall -q app alembic tests
python -m alembic current
python -m alembic upgrade head
```

No database migration is required.
