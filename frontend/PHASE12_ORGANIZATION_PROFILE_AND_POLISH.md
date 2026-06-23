# Phase 12 - Organization Profile and UI/UX Polish

## Frontend Route

- `/dashboard/organization-profile`

The route is listed under Administration as `Organization Profile` and is intended for Admin users only.

## Page Features

- View current organization profile
- Edit organization name and short name
- Upload/change/delete logo
- Maintain address, city, district, province, and country
- Maintain phone, email, and website
- Maintain registration and tax numbers
- Configure report footer text, watermark text, and report colors
- Configure authorized signatory details
- Preview report header identity card

## Form Sections

1. Basic Information
2. Address
3. Contact Details
4. Report Branding
5. Authorized Signatory

## Logo Behavior

The logo endpoint is protected by backend authentication. The page loads the logo as a blob using the stored bearer token and displays it as a safe object URL. The frontend never receives or displays the backend absolute filesystem path.

## Report Branding Behavior

PDF exports use backend organization profile branding. When a profile is missing, reports continue to display the generic CCMS fallback branding.

## UI/UX Polish Completed

- Admin sidebar link added under Administration
- Professional organization identity card
- Clear form grouping
- Save/upload/delete feedback messages
- Loading, success, and error states
- Required-field markers for organization name and short name
- Logo upload guidance

## Permission Behavior

- Admin can manage the profile.
- Non-admin users are blocked from the settings UI.
- Existing dashboard/sidebar/module behavior is preserved.

## Manual Swagger / Browser Testing

1. Login as `admin` / `Admin123`.
2. Open `/dashboard/organization-profile`.
3. Enter organization details and save.
4. Upload a PNG/JPG/JPEG/WEBP logo.
5. Download `/exports/children.pdf`.
6. Download `/exports/daily-attendance.pdf`.
7. Download `/exports/daily-visitor-register.pdf`.
8. Confirm header/footer branding appears.
9. Login as Viewer and confirm the page is not editable.

## Testing Commands

```powershell
cd C:\Users\Yasir\Downloads\cms\frontend
npm run typecheck
npm run build
```

## Known Limitations

- Existing logo preview requires an authenticated session.
- Watermark text is captured for future PDF rendering but not drawn as a watermark in this polish pass.
