# CCMS Environment Variables

Create backend and frontend environment files from their examples. Never commit real secrets.

## Backend

File:

```text
C:\Users\Yasir\Downloads\cms\backend\.env
```

Important variables:

| Variable | Purpose |
| --- | --- |
| `PROJECT_NAME` | API display name. |
| `ENVIRONMENT` | `local`, `staging`, or `production`. |
| `DEBUG` | Use `false` outside local debugging. |
| `DATABASE_URL` | SQLAlchemy database URL. |
| `SECRET_KEY` | JWT signing secret; must be strong and private. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Login token lifetime. |
| `BACKEND_CORS_ORIGINS` | Allowed frontend origins. |
| `UPLOAD_DIR` | Folder for uploaded files. |
| `RATE_LIMIT_ENABLED` | Enables request rate limiting where configured. |
| `ADMIN_USERNAME` | Optional bootstrap administrator username. |
| `ADMIN_PASSWORD` | Optional bootstrap password; do not keep a weak value. |

Local backend URL:

```text
http://127.0.0.1:8000
```

## Frontend

File:

```text
C:\Users\Yasir\Downloads\cms\frontend\.env.local
```

Required local setting:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Use the deployed API URL for staging or production.

## Security notes

- Do not commit `.env` or `.env.local`.
- Rotate `SECRET_KEY` before production use.
- Change local demo passwords before real staff training.
- Do not store real child data in demo or test databases.
