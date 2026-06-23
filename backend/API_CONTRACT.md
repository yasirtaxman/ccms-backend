# CCMS API Contract

## Connection and authentication

Local base URL: `http://127.0.0.1:8000`. Swagger is at `/docs`; OpenAPI is at `/openapi.json`.

Login with `POST /auth/login` using `username_or_email` and `password`, or use OAuth2 `POST /auth/token`. Send the returned token as `Authorization: Bearer <token>`. `GET /auth/me` returns the current safe user profile. `GET /users/me/permissions` returns roles and a frontend-oriented effective-permission summary.

Default roles:

- Admin: unrestricted administration (`*`).
- Manager: operational dashboards, records, reports, exports, and import commit.
- Data Entry Operator: record entry, safe reports/exports, and import preview.
- Viewer: safe read-only dashboards, reports, and exports.

## User administration

Admin-only endpoints are `GET /users`, `GET /users/{id}`, `POST /users`, `PUT /users/{id}`, `POST /users/{id}/roles`, `/activate`, `/deactivate`, and `/reset-password`. Authenticated users change their own password at `POST /auth/change-password`. Passwords and hashes are never returned.

## Standard responses

New system utilities use:

```json
{"success":true,"message":"string","data":{},"errors":null,"meta":{}}
```

Errors use `success: false`, `data: null`, and an `errors` array containing `field`, `message`, and `code`. Existing business endpoints retain their established response bodies for backward compatibility. Every response includes `X-Request-ID`.

## Module endpoints

- Children/documents: `/children`, `/documents`, `/children/{id}/documents`.
- Sponsors: `/sponsors`, `/child-sponsorships`.
- Accommodation: `/buildings`, `/blocks`, `/floors`, `/rooms`, `/beds`, `/bed-allocations`.
- Medical: `/children/{id}/medical-profile`, medical visits, medications, vaccinations, documents.
- Education: schools, education records, exam results, attendance, documents.
- Case Management: case profiles, notes, counseling, incidents, care plans, reviews.
- Dashboards: `/dashboard/executive`, `/dashboard/operational`, `/dashboard/alerts`.
- Reports: `/reports/consolidated/*`; pagination uses `limit` and `offset`, with endpoint-specific query filters.
- Imports: template download and multipart `file` upload at `/imports/children/preview` and `/imports/children/commit`.
- Exports: authenticated `.xlsx` and `.pdf` endpoints under `/exports`.
- Daily child attendance: individual history under `/children/{id}/daily-attendance`; register operations under `/daily-attendance`; transactional bulk marking at `/daily-attendance/bulk-mark`; today/dashboard summaries and daily/monthly reports. This is organization presence attendance and is separate from academic Education Attendance.

File uploads use `multipart/form-data`, restricted extensions, sanitized filenames, configured size limits, and server-controlled storage paths. Frontend menus should use `/users/me/permissions`, not hardcoded assumptions alone.
