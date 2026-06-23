# CCMS Phase 10 — Children Frontend

## Workspace delivered

Created real routes for Children list, create, profile, edit, import, daily attendance, and attendance reports. Added typed Children/attendance contracts, one shared API service, and components for tables, forms, profile summaries, documents, exports, imports, attendance bulk marking, status badges, and reports. Updated navigation, API errors, responsive styles, and README guidance.

Created files include all seven routes listed below; `types/children.ts`, `types/attendance.ts`, and `lib/children.ts`; plus `components/children/ChildrenTable.tsx`, `ChildForm.tsx`, `ChildProfileHeader.tsx`, `ChildProfileSummary.tsx`, `ChildDocumentsPanel.tsx`, `ChildImportPanel.tsx`, `ChildExportButtons.tsx`, `DailyAttendanceRegister.tsx`, `DailyAttendanceBulkForm.tsx`, `AttendanceStatusBadge.tsx`, and `AttendanceReportsPanel.tsx`.

Modified files: `lib/routes.ts`, `lib/api.ts`, `app/globals.css`, and `README.md`.

Routes:

- `/dashboard/children`
- `/dashboard/children/new`
- `/dashboard/children/[id]`
- `/dashboard/children/[id]/edit`
- `/dashboard/children/import`
- `/dashboard/children/attendance`
- `/dashboard/children/attendance/reports`

The list provides client-side search/filter/pagination against the existing Children API. Forms match the backend create and immutable-safe update contracts. Profile screens combine the core child, complete safe summary, documents, attendance, and authenticated exports. Viewer-sensitive guardian identifiers and full addresses are hidden.

The existing profile download controls continue to call the authenticated full-profile PDF and Excel endpoints. These downloads now produce the professional A4 profile report and structured multi-sheet workbook; no route or user workflow changed. The complete profile summary also displays the safe daily attendance summary returned by the backend.

Import follows template download → Excel/CSV upload → preview → correction → transactional commit. Admin/Manager can commit, Data Entry Operator can preview, and Viewer is blocked. Attendance supports date selection, status/time/remarks entry, Mark All Present, unsaved reset, transactional save, summary cards, read-only Viewer mode, date-range reports, and monthly percentages.

## Validation

```powershell
npm install
npm run typecheck
npm run lint
npm run build
```

## Manual checklist

1. Start backend from `C:\Users\Yasir\Downloads\cms\backend` with `.venv`, `PYTHONPATH=.`, and `uvicorn app.main:app --reload`.
2. Start frontend from `C:\Users\Yasir\Downloads\cms\frontend` with `npm run dev`.
3. Open `http://localhost:3000/login`; use `admin` / `Admin123`.
4. Confirm `/dashboard/children` loads and supports search, filters, pagination, and exports.
5. Create, view, and edit a child; inspect profile summary and documents.
6. Upload, verify, and Admin-delete an admission document.
7. Download the import template, preview data, correct errors, and commit a valid file.
8. Open daily attendance, select today, Mark All Present, save, change one Medical Leave, and save again.
9. Run daily and monthly attendance reports.
10. Sign in as Viewer and verify all Children and attendance mutation controls are absent.
