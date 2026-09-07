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

The local Angular build uses `http://localhost:8000`. The production build
uses `https://find-location-api.onrender.com` from
`src/environments/environment.prod.ts`.

On Render, set:

```text
ADMIN_API_KEY=the-same-secure-admin-key-used-by-the-admin
FRONTEND_ORIGINS=http://localhost:4200,http://127.0.0.1:4200,https://ekkalurusubhash.github.io
```

The default SQLite database is `locations.db`. Set `LOCATION_DATABASE` to a
persistent path when deploying the API. The admin API key must be kept only on
the server; do not put it in the Angular source code.