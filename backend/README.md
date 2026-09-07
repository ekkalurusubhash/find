# FastAPI location backend

## Local setup

```powershell
python -m pip install -r backend/requirements.txt
$env:ADMIN_API_KEY = "replace-with-a-long-random-key"
$env:FRONTEND_ORIGINS = "http://localhost:4200"
uvicorn backend.main:app --reload --port 8000
```

The Angular app sends approved browser coordinates to `POST /api/locations`.
The admin screen reads recent records from `GET /api/locations` with the
`X-Admin-Key` header.

For deployment, set `FRONTEND_ORIGINS` to the exact GitHub Pages origin, such
as `https://your-user.github.io`, and configure the same API URL in
`src/app/services/location.service.ts` before building the Angular app.

The default SQLite database is `locations.db`. Set `LOCATION_DATABASE` to a
persistent path when deploying the API. The admin API key must be kept only on
the server; do not put it in the Angular source code.