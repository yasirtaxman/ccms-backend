# CCMS Phase 6: Case Management and Child Progress Notes

Phase 6 provides professional child case histories, role-sensitive progress notes,
counseling sessions, incidents, care plans, case reviews, reports, dashboard alerts,
soft deletion, RBAC, and transactional auditing. No unrelated financial, donation, HR,
inventory, or store module was introduced.

## Files created

- `app/models/case_management.py`
- `app/schemas/case_management.py`
- `app/api/v1/case_management.py`
- `alembic/versions/f6a04c9e3b72_add_case_management.py`
- `tests/test_case_management.py`
- `PHASE6_IMPLEMENTATION.md`

## Files modified

- `app/services/audit.py`: case modules and 23 workflow actions.
- `app/main.py`: case-management router registration.
- `alembic/env.py`: case-management metadata import.
- `create_tables.py`: case-management models added to the legacy helper.

## Migration

- Revision: `f6a04c9e3b72`
- Previous revision: `e5f93b8d2a61`
- Tables: `child_case_profiles`, `case_notes`, `counseling_sessions`,
  `incident_records`, `care_plans`, `case_reviews`
- Every table includes nullable `organization_id`, actor/timestamp tracking, and
  `deleted_at`/`deleted_by`.
- Includes all requested foreign keys, indexes, check/unique constraints, and a
  PostgreSQL partial unique index for one non-deleted Active care plan per child and
  goal area.

```powershell
alembic upgrade head
alembic downgrade e5f93b8d2a61
```

Offline downgrade SQL requires an explicit Alembic range:

```powershell
python -m alembic downgrade f6a04c9e3b72:e5f93b8d2a61 --sql
```

## Models added

- `ChildCaseProfile`: one unique case profile and case number per child.
- `CaseNote`: filtered Normal, Confidential, and Restricted case notes with follow-ups.
- `CounselingSession`: scheduled/completed/cancelled counseling history.
- `IncidentRecord`: severity alerts and privileged review/close workflows.
- `CarePlan`: historical child goals with one active plan per goal area.
- `CaseReview`: pending/completed/cancelled periodic review history.

Historical records are never physically deleted. Every DELETE endpoint sets
`deleted_at`, `deleted_by`, and `updated_by` and writes its audit event transactionally.

## RBAC rules

| Capability | Admin | Manager | Data Entry Operator | Viewer |
|---|---:|---:|---:|---:|
| View ordinary case data | Yes | Yes | Yes | Yes |
| Create/update ordinary records | Yes | Yes | Yes | No |
| View Confidential notes | Yes | Yes | Yes | No |
| View Restricted notes | Yes | Yes | No | No |
| Close case | Yes | Yes | No | No |
| Reopen case | Yes | No | No | No |
| Review/close incident | Yes | Yes | No | No |
| Complete/cancel care plan | Yes | Yes | Yes | No |
| Soft-delete records | Yes | No | No | No |

Unauthorized note retrieval returns 404 to avoid disclosing that a protected note exists.
Closed case profiles are editable only by Admin, and status workflows cannot be bypassed
through general update endpoints.

## Audit modules

- `CASE_MANAGEMENT`
- `CASE_PROFILE`
- `CASE_NOTE`
- `COUNSELING`
- `INCIDENT`
- `CARE_PLAN`
- `CASE_REVIEW`

## Audit actions

- `CASE_PROFILE_CREATE`, `CASE_PROFILE_UPDATE`, `CASE_PROFILE_CLOSE`, `CASE_PROFILE_REOPEN`
- `CASE_NOTE_CREATE`, `CASE_NOTE_UPDATE`, `CASE_NOTE_DELETE`
- `COUNSELING_SESSION_CREATE`, `COUNSELING_SESSION_UPDATE`, `COUNSELING_SESSION_DELETE`
- `INCIDENT_CREATE`, `INCIDENT_UPDATE`, `INCIDENT_REVIEW`, `INCIDENT_CLOSE`, `INCIDENT_DELETE`
- `CARE_PLAN_CREATE`, `CARE_PLAN_UPDATE`, `CARE_PLAN_COMPLETE`, `CARE_PLAN_CANCEL`, `CARE_PLAN_DELETE`
- `CASE_REVIEW_CREATE`, `CASE_REVIEW_UPDATE`, `CASE_REVIEW_DELETE`

## Endpoints added

### Case profiles

- `POST/GET/PUT /children/{child_id}/case-profile`
- `POST /children/{child_id}/case-profile/close`
- `POST /children/{child_id}/case-profile/reopen`

### Case notes

- `POST/GET /children/{child_id}/case-notes`
- `GET/PUT/DELETE /case-notes/{note_id}`
- List filters: `note_type`, `visibility`, `follow_up_required`, `from_date`, `to_date`

### Counseling

- `POST/GET /children/{child_id}/counseling-sessions`
- `GET/PUT/DELETE /counseling-sessions/{session_id}`

### Incidents

- `POST/GET /children/{child_id}/incidents`
- `GET/PUT/DELETE /incidents/{incident_id}`
- `POST /incidents/{incident_id}/review`
- `POST /incidents/{incident_id}/close`
- List filters: `severity`, `incident_type`, `review_status`, `from_date`, `to_date`

### Care plans

- `POST/GET /children/{child_id}/care-plans`
- `GET/PUT/DELETE /care-plans/{plan_id}`
- `POST /care-plans/{plan_id}/complete`
- `POST /care-plans/{plan_id}/cancel`

### Case reviews

- `POST/GET /children/{child_id}/case-reviews`
- `GET/PUT/DELETE /case-reviews/{review_id}`

## Reports

- `GET /reports/case-profiles`
- `GET /reports/open-cases`
- `GET /reports/closed-cases`
- `GET /reports/high-risk-children`
- `GET /reports/critical-risk-children`
- `GET /reports/pending-follow-ups`
- `GET /reports/upcoming-case-reviews`
- `GET /reports/upcoming-counseling-sessions`
- `GET /reports/critical-incidents`
- `GET /reports/pending-incident-reviews`
- `GET /reports/active-care-plans`
- `GET /reports/completed-care-plans`

Role-sensitive follow-up reports and dashboard counts exclude notes the current user is
not permitted to see.

## Dashboard

`GET /dashboard/case-management` returns all twelve requested counters, including
critical-risk profiles, unresolved critical incidents, due follow-ups, upcoming reviews
and counseling sessions, active care plans, and children without a case profile.

## Tests and verification

```powershell
pytest -q -p no:cacheprovider tests
python -m compileall -q app alembic tests
python -m alembic upgrade head --sql
python -m alembic downgrade f6a04c9e3b72:e5f93b8d2a61 --sql
git diff --check
```

Result:

```text
19 passed
```

Tests cover profile lifecycle and duplication, closed-case protection, all note visibility
levels, follow-ups, counseling, incident review/close, active-plan uniqueness,
complete/cancel workflows, case reviews, soft deletion, reports, dashboard, RBAC, and
every audit workflow.

## Swagger verification checklist

- [x] Router registered and OpenAPI generation succeeds.
- [x] Strict response models attached to all record endpoints.
- [x] Enum values and validation constraints appear in request schemas.
- [x] Note and incident filters appear as typed query parameters.
- [x] OAuth2 authorization applies to every endpoint.
- [x] Case Management, Reports, and Dashboard tags are visible at `/docs`.
- [x] Existing routes remain unchanged.

## Manual Swagger test workflow

1. Login as Admin.
2. Create child if needed.
3. Create case profile.
4. Add case note.
5. Add counseling session.
6. Add incident.
7. Review incident.
8. Create care plan.
9. Complete care plan.
10. Create case review.
11. Check dashboard.
12. Check reports.
13. Check audit logs.
14. Test Viewer restrictions.
15. Test Restricted note access.

## Final verification checklist

- [x] Branch `phase6-case-management` created.
- [x] No unrelated module implemented.
- [x] Six operational tables use full tracking and soft-delete fields.
- [x] Historical records cannot be physically deleted through the API.
- [x] One profile per child and unique case number enforced.
- [x] Closed-case and privileged workflow rules enforced.
- [x] Active care-plan uniqueness enforced in API and PostgreSQL.
- [x] All requested date validations enforced.
- [x] Every write operation audited.
- [x] Migration upgrade and downgrade SQL verified.
- [x] Full Phase 1–6 test suite passed.
