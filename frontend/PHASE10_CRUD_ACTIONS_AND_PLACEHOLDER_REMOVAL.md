# CCMS Phase 10 - CRUD Actions and Report Controls

## Pages updated

All operational sidebar workspaces now use the shared authenticated CRUD interface. Sponsors, sponsorships, buildings, rooms and beds, bed allocations, medical profiles and activity, education, case management, users, and roles expose create forms generated from the backend OpenAPI schemas. Forms use labels, required indicators, enum dropdowns, date/number inputs, and selectors for child, sponsor, accommodation, school, education-record, and role relationships.

Every data table provides View. Authorized roles receive Edit where the backend has an update endpoint. Admin-only delete actions are available for sponsors, buildings, beds, schools, case notes, counseling sessions, incidents, care plans, and case reviews. Bed allocations provide Transfer and Vacate. Case profiles provide Close and Admin-only Reopen. Incidents provide Manager/Admin Review and Close. Care plans provide Complete and Cancel. Users provide role assignment, activation, deactivation, and password reset. All lifecycle and destructive operations use confirmation, backend error display, success feedback, and automatic refresh.

Children retain their dedicated Add, View, Edit, import, document, and export workflows. No child hard-delete action was added because the backend does not expose one. Admission Documents now provides a child selector and the full upload, checklist, verification, and Admin delete panel directly on its sidebar page.

## Reports and exports

Each major operational workspace provides PDF and Excel buttons backed by the existing consolidated export endpoints. The reports page can run or export the selected report. The exports page includes general report downloads plus child-specific Full Profile and month/year attendance exports. Daily attendance links directly to its filter-aware reporting and export workspace.

## Permissions

- Admin: full configured create/edit/lifecycle/delete access plus Admin-only user and audit exports.
- Manager: operational create/edit actions and Manager lifecycle actions.
- Data Entry Operator: backend-authorized data-entry create/edit actions.
- Viewer: View and safe exports only; mutation controls are not rendered.

Frontend controls use the existing permission state loaded from `GET /users/me/permissions`. Backend authorization remains authoritative.

## Known limitations

No unsafe hard-delete endpoint was invented. Modules without backend record deletion use their supported status or lifecycle update. Medical and education document deletion remains available through their child-specific document APIs but is not duplicated in general report tables. Role update/delete is omitted because the backend only supports role creation, listing, and assignment.

## Validation

```powershell
npm run typecheck
npm run build
```
