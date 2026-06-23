# Phase 11 Frontend: Visitors and Detailed RBAC

## Routes

- `/dashboard/visitors` — visitor list, search, create, edit, verify, block, activate/deactivate, and exports.
- `/dashboard/child-visits` — meeting list, scheduling, approval/rejection, check-in/check-out, cancellation, and exports.
- `/dashboard/visitor-reports` — daily/monthly filters, results, PDF and Excel downloads.
- `/dashboard/roles` — role selector, grouped permission matrix, role creation, custom-role deletion, and permission saving.
- `/dashboard/children/{id}` — child profile with visitor/meeting history and permission-aware attendance/documents.

## Permission-Aware Interface

Navigation, create/edit buttons, row actions, exports, child documents, and attendance controls use effective permissions returned by the backend. Admin retains all actions. Warden sees only dashboard, limited children/accommodation, attendance, visitors, and child meetings allowed by its permission set. Hiding controls is usability protection; the backend remains the authorization authority.

The Roles page groups permissions by module, supports select-all per module, protects the Admin role, and asks for confirmation before deleting a custom role.

## Visitor and Meeting Workflow

Create a visitor, verify identity, schedule a child meeting, approve or reject it, check an approved meeting in, and check it out. Status-specific buttons appear only when the signed-in user has the corresponding permission. Visitor reports support daily/monthly filters and privacy-safe PDF/Excel exports.

## Validation

```powershell
cd C:\Users\Yasir\Downloads\cms\frontend
npm run typecheck
npm run build
```

Manual test: sign in as `admin/Admin123`, complete the visitor-to-checkout flow, open reports and exports, update Warden permissions under Roles, then sign in as a Warden and confirm its pages/actions match the saved matrix. Repeat with Viewer to confirm read-only behavior.

## Known Limitations

- The phase prepares responsive web screens and APIs for future Android use; it does not ship an Android application.
- Visitor photo binary upload is not added because the current visitor workflow stores an optional path only.
