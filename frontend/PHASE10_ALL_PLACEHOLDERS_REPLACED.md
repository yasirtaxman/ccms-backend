# CCMS Phase 10 - All Sidebar Workspaces Implemented

Every sidebar destination now opens a useful page. Existing Children, import, daily attendance, and attendance-report screens remain dedicated workflows. Sponsors, sponsorships, accommodation, medical, education, case management, exports, imports, users, roles, audit logs, and system status use authenticated data-backed workspaces with refresh, search, loading, empty, and error states. Consolidated Reports has a six-module report selector.

## Routes and APIs

- Child management: `/dashboard/children`, `/dashboard/admission-documents`, `/dashboard/children/attendance`, `/dashboard/children/attendance/reports`, and `/dashboard/children/import`.
- Sponsorship: `/sponsors` and `/reports/active-sponsorships`.
- Accommodation: `/buildings`, `/beds`, `/bed-allocations`, and `/reports/occupancy`.
- Medical: medical profile, visit, active medication, and upcoming vaccination reports.
- Education: `/schools`, student, exam-result, and low-attendance reports.
- Case management: case profiles, pending follow-ups, counseling sessions, incidents, care plans, and case reviews.
- Administration: `/users`, `/roles`, `/audit-logs`, `/system/readiness`, and `/system/info`.

Viewer mutation controls remain hidden. Admin, Manager, and Data Entry Operator behavior follows the existing role helpers and backend authorization. Sensitive identifiers, full addresses, diagnoses, treatment details, credentials, and restricted note fields are excluded from generic tables.

## Admission documents

Draft children can be created and retain their status until staff deliberately change it. The profile document panel downloads the approved type definitions and checklist, requires dropdown selection, restricts the file picker to permitted extensions, displays required/optional items, and shows uploaded and verified progress. The admission documents page explains the workflow and links to Children and imports.

## Attendance

The daily register displays Room and Bed and uses `Not allocated` when there is no active allocation. Reports display the same accommodation context and provide filter-aware Daily PDF/Excel and Monthly PDF/Excel downloads. Viewer access remains read-only.

## Known limitations

Module workspaces are read-first summaries and lists. The existing backend supports additional record-specific mutations, but dedicated create/edit forms are currently concentrated in Children, admission documents, imports, and daily attendance. Child photos appear in the full-profile PDF when a valid uploaded image is available; the profile header otherwise retains its initials display.

## Validation

```powershell
npm run typecheck
npm run build
```
