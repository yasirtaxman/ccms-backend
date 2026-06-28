# Phase 13 - Child Development, Behavior & Talent Profile

## Frontend Routes

- `/dashboard/development/observations`
- `/dashboard/development/observations/new`
- `/dashboard/development/observations/[id]`
- `/dashboard/development/observations/[id]/edit`
- `/dashboard/development/indicators`
- `/dashboard/development/reports`
- `/dashboard/children/[id]/development`

Sidebar group:

- Development Profile

## Components

- `DevelopmentObservationsTable`
- `DevelopmentObservationForm`
- `DevelopmentIndicatorField`
- `DevelopmentIndicatorsAdmin`
- `DevelopmentReportsPanel`
- `ChildDevelopmentSummary`

## Observation Form UX

The form uses grouped category cards and system-defined indicators. It supports:

- Monthly, weekly, and as-needed observations
- Save draft
- Submit for review
- Dropdowns, checkboxes, rating fields, yes/no fields, and notes
- Progress indicator
- Urgent warning when high-risk indicators are selected
- Recommended support requirement for urgent observations

The UI uses safe wording and presents observations as current indicators for support planning only.

## Child Profile Integration

Child profile now shows Development, Behavior & Talent Profile with:

- latest observation date
- monthly review status
- strongest positive strengths
- support needs
- possible areas of interest
- risk flags requiring review
- next review date
- Add Observation button
- Export Development Profile PDF button

## Reports

Development Reports page includes:

- monthly missing observation report
- child development observations PDF
- monthly development summary PDF
- child talent summary PDF

All PDF exports use backend Phase 12 report branding.

## Permission Behavior

Navigation and actions are permission-aware:

- Warden can create and submit limited observations.
- Viewer cannot create or edit observations.
- Admin manages indicators.
- Admin, Manager, and Counselor review/close observations.

## Testing Commands

```powershell
cd C:\Users\Yasir\Downloads\cms\frontend
npm run typecheck
npm run build
```

## Known Limitations

- The module provides support guidance only and does not automate career decisions.
- Sensitive notes are protected by backend permissions; UI visibility follows API response filtering.
