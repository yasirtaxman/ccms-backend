# CCMS Phase 9 Frontend Foundation

## Implementation

The existing empty `frontend` directory was initialized in place as a Next.js 16 TypeScript App Router application. No nested frontend or output directory was created. The foundation uses React 19, Tailwind CSS 4, lucide-react, Axios, React Hook Form, and Zod.

Created application routes: `/`, `/login`, `/dashboard`, `/dashboard/[...slug]`, and `/unauthorized`. Module links resolve to professional next-phase cards rather than incomplete CRUD interfaces.

Created auth and layout components include `AuthProvider`, `LoginForm`, `ProtectedRoute`, `PermissionGate`, `AppSidebar`, `Topbar`, `UserMenu`, and `DashboardShell`. Shared hooks expose auth and permission state. Backend-aligned TypeScript contracts cover users, roles, permissions, OAuth login, and the executive dashboard.

## Authentication and API client

Login sends OAuth2 form data to `POST /auth/token`, stores the access token for development, loads `/auth/me` plus `/users/me/permissions`, and redirects to the protected dashboard. Axios attaches the token once through an interceptor; HTTP 401 clears the session and redirects to login. Tokens are never logged. Production can later replace local storage with an httpOnly-cookie/BFF strategy without changing screen contracts.

## Navigation and dashboard

Navigation groups cover every current backend module. Central role helpers filter sensitive administration, imports, and case-management entries. The responsive dashboard shell contains a mobile sidebar, topbar, user identity/roles, and logout.

`/dashboard` consumes `/dashboard/executive`, renders nine operational metric cards plus alerts and pending-action summaries, and handles loading, empty, and error states.

## Environment and validation

`NEXT_PUBLIC_API_BASE_URL` defaults locally to `http://127.0.0.1:8000` and is documented in `.env.example`.

Commands:

```powershell
npm install
npm run typecheck
npm run lint
npm run build
```

The backend compatibility suite is run separately from `backend` with `python -m pytest tests -q -p no:cacheprovider`.

## Known limitations and next phases

Module pages are placeholders, charts are intentionally omitted, and password-change UI is deferred. Next phases should implement CRUD workspaces module by module, add notification/toast infrastructure and end-to-end browser tests, and evaluate secure httpOnly token delivery for production.

At validation time, `npm audit --omit=dev` reported two moderate advisories in the PostCSS version bundled by Next.js 16.2.9. npm offered only a forced downgrade to an obsolete major Next.js release, so no unsafe automated downgrade was applied. Recheck the advisory when the next compatible Next.js patch is available.
