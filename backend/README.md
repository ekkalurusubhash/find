# FastAPI location backend

## Local setup

```powershell
python -m pip install -r backend/requirements.txt
$env:ADMIN_API_KEY = "replace-with-a-long-random-key"
$env:FRONTEND_ORIGINS = "http://localhost:4200,http://127.0.0.1:4200"
uvicorn backend.main:app --reload --port 8000
```

The Angular app sends approved browser coordinates to `POST /api/locations`.
The admin screen reads recent records from `GET /api/locations` with the
`X-Admin-Key` header.
The public home page reads up to 10 headlines from `GET /api/headlines`.
Configure them on the server with `HEADLINES_JSON`, for example:

```powershell
$env:HEADLINES_JSON = '[{"title":"A new local story","source":"Local desk","url":"https://example.com/story","published_at":"2026-09-07T10:00:00+00:00"}]'
```

The local Angular build uses `http://localhost:8000`. The production build
uses `https://find-location-api.onrender.com` from
`src/environments/environment.prod.ts`.

On Render, set:

```text
ADMIN_API_KEY=the-same-secure-admin-key-used-by-the-admin
FRONTEND_ORIGINS=http://localhost:4200,http://127.0.0.1:4200,https://ekkalurusubhash.github.io
HEADLINES_JSON=[{"title":"A new local story","source":"Local desk","url":"https://example.com/story","published_at":"2026-09-07T10:00:00+00:00"}]
```

Local development uses the SQLite database `locations.db`. For Render, create
a managed PostgreSQL database and add its internal connection string as the
`DATABASE_URL` environment variable. The API automatically uses PostgreSQL
when `DATABASE_URL` is present and SQLite otherwise. This keeps location data
across deploys and restarts.

On Render, add:

```text
DATABASE_URL=the-internal-PostgreSQL-connection-string
```

Do not commit or expose `DATABASE_URL`; the admin API key must also remain only
on the server.