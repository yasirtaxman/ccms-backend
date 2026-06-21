# CCMS Frontend

Next.js App Router frontend foundation for the Child Care Management System.

## Setup

```powershell
cd C:\Users\Yasir\Downloads\cms\frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000` and run the CCMS backend before signing in. Production API URLs must come from the deployment environment.

Development login:

- Username: `admin`
- Password: `Admin123`
- Backend must be running at `http://127.0.0.1:8000`

These credentials are for the existing local development account. Password policy applies when creating, resetting, or changing passwords; it does not reject an existing password during login.

## Authentication

The login form posts OAuth2 form data to `/auth/token`, stores the development token in `localStorage`, fetches `/auth/me` and `/users/me/permissions`, and redirects to `/dashboard`. The shared API client attaches the bearer token and clears the session on HTTP 401. Logout also clears the session. A secure httpOnly cookie/BFF strategy is recommended for a later production frontend phase.

## Structure

- `app`: login, protected dashboard, unauthorized route, and professional module placeholders.
- `components/auth`: provider, route protection, permission gate, and login form.
- `components/layout`: responsive sidebar, topbar, shell, and user menu.
- `hooks`: shared authentication and permission access.
- `lib`: API client, token storage, permission helpers, navigation, and utilities.
- `types`: backend-aligned user, authentication, permissions, and dashboard contracts.

Navigation items are filtered centrally through `lib/routes.ts` and `lib/permissions.ts`. Admin receives administration items; operational roles receive safe module navigation; Viewer does not receive imports or sensitive case-management links.

## Commands

```powershell
npm run dev
npm run typecheck
npm run lint
npm run build
npm run start
```

Phase 9 deliberately leaves module CRUD pages as polished placeholders. Subsequent phases can implement each workspace using the existing shell, API client, auth state, permissions, loading states, and error patterns.

## Children and daily attendance

Phase 10 implements the Children workspace at `/dashboard/children`, including create/edit/profile, admission documents, imports, authenticated exports, and daily organization presence attendance. Daily attendance is separate from academic Education Attendance. Admin and Manager receive full operational controls, Data Entry Operator can maintain records and preview imports, and Viewer receives read-only screens.
