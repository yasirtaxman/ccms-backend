# Phase 13 - Child Development, Behavior & Talent Profile

## Purpose

Phase 13 adds a structured observation module for monthly, weekly, and as-needed child development monitoring. It is designed for welfare support, safe observation, career guidance, and follow-up planning.

This module does not provide medical or psychological assessment. It uses safe wording such as observed tendency, current indicator, suggested support, possible area of interest, needs attention, requires counselor review, and follow-up recommended.

## Backend Models

- `DevelopmentIndicator`
- `ChildDevelopmentObservation`
- `ChildDevelopmentObservationResponse`

## Indicator Catalogue

Default indicators are system-defined and seeded idempotently. Users select indicators from the catalogue instead of typing indicator names manually.

Categories:

1. Personal Hygiene & Cleanliness
2. Discipline & Responsibility
3. Social Behavior
4. Emotional Wellbeing
5. Confidence & Communication
6. Learning Behavior
7. Talent & Interests
8. Physical Activity & Sports
9. Digital Behavior & Screen Awareness
10. Safety & Risk Indicators
11. Spiritual / Moral Development
12. Career / Field Suitability Indicators
13. Support Needs
14. Positive Strengths

Input types:

- checkbox
- dropdown
- rating_1_to_5
- yes_no
- multi_select
- short_note

## Observation Workflow

Supported frequencies:

- Monthly
- Weekly
- As Needed
- Incident Based
- Counselor Review
- Teacher Review
- Warden Review

Review statuses:

- Draft
- Submitted
- Reviewed
- Needs Follow-up
- Closed
- Archived

Workflow:

1. Permitted users create a draft observation.
2. Creator can submit for review.
3. Admin, Manager, or Counselor can review.
4. Admin, Manager, or Counselor can mark Needs Follow-up.
5. Admin, Manager, or Counselor can close.
6. Admin/Manager can archive where permitted.

## Backend Endpoints

- `GET /development-indicators`
- `POST /development-indicators`
- `PUT /development-indicators/{id}`
- `POST /development-indicators/{id}/activate`
- `POST /development-indicators/{id}/deactivate`
- `GET /child-development-observations`
- `POST /child-development-observations`
- `GET /child-development-observations/{id}`
- `PUT /child-development-observations/{id}`
- `DELETE /child-development-observations/{id}`
- `GET /children/{child_id}/development-profile`
- `GET /children/{child_id}/development-observations`
- `GET /children/{child_id}/development-summary`
- `POST /child-development-observations/{id}/submit`
- `POST /child-development-observations/{id}/review`
- `POST /child-development-observations/{id}/close`
- `POST /child-development-observations/{id}/archive`
- `GET /reports/child-development`
- `GET /reports/monthly-development-missing`
- `GET /reports/child-talent-summary`
- `GET /dashboard/development`

PDF exports:

- `GET /exports/child-development-profile/{child_id}.pdf`
- `GET /exports/child-development-observations.pdf`
- `GET /exports/monthly-development-summary.pdf`
- `GET /exports/child-talent-summary.pdf`

All PDFs use Phase 12 organization profile branding.

## Permissions

Added permissions:

- `development.view`
- `development.create`
- `development.update`
- `development.delete`
- `development.submit`
- `development.review`
- `development.close`
- `development.export`
- `development.indicators.view`
- `development.indicators.manage`
- `development.sensitive_notes.view`
- `development.sensitive_notes.create`

Default behavior:

- Admin: all permissions
- Manager: development view/create/update/review/close/export
- Data Entry Operator: create/update/submit through default write permissions
- Warden: limited view/create/submit
- Viewer: limited view only
- Counselor: created with view/create/update/submit/review/close/export and sensitive notes permissions

## Privacy Rules

Sensitive indicators and private notes are hidden from users without sensitive-note permission. PDF exports avoid confidential counseling notes, medical assessment details, guardian CNIC, sponsor details, and other restricted data.

Urgent indicators require recommended support notes and are treated as follow-up recommendations, not final conclusions.

## Audit Actions

- `DEVELOPMENT_INDICATOR_CREATED`
- `DEVELOPMENT_INDICATOR_UPDATED`
- `DEVELOPMENT_INDICATOR_ACTIVATED`
- `DEVELOPMENT_INDICATOR_DEACTIVATED`
- `CHILD_DEVELOPMENT_OBSERVATION_CREATED`
- `CHILD_DEVELOPMENT_OBSERVATION_UPDATED`
- `CHILD_DEVELOPMENT_OBSERVATION_SUBMITTED`
- `CHILD_DEVELOPMENT_OBSERVATION_REVIEWED`
- `CHILD_DEVELOPMENT_OBSERVATION_CLOSED`
- `CHILD_DEVELOPMENT_OBSERVATION_ARCHIVED`

## Testing Commands

```powershell
cd C:\Users\Yasir\Downloads\cms\backend
$env:PYTHONPATH="."
python -m alembic upgrade head
python -m pytest tests -q -p no:cacheprovider
python -m compileall -q app alembic tests
```

## Manual Test Checklist

1. Login as admin/Admin123.
2. Open Development Observations.
3. Add observation for a child.
4. Confirm indicators appear as dropdowns, checkboxes, and rating fields.
5. Save draft.
6. Submit for review.
7. Review and close as Admin/Manager/Counselor.
8. Open child profile and confirm Development Profile section.
9. Export Child Development Profile PDF and confirm organization branding.
10. Confirm no unsafe labeling language appears.
11. Activate/deactivate indicators.
12. Confirm Development permissions appear on Roles page.
13. Login as Warden and confirm limited access.
14. Login as Viewer and confirm no create/edit sensitive access.
