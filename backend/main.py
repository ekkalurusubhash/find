from datetime import datetime, timezone
import json
from pathlib import Path
import os
import sqlite3

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


DATABASE_PATH = Path(os.getenv("LOCATION_DATABASE", "locations.db"))
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
DEFAULT_FRONTEND_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "https://ekkalurusubhash.github.io",
]
CONFIGURED_FRONTEND_ORIGINS = [
    origin.strip().strip('"\'').rstrip("/")
    for origin in os.getenv("FRONTEND_ORIGINS", "").split(",")
    if origin.strip()
]
FRONTEND_ORIGINS = list(dict.fromkeys(DEFAULT_FRONTEND_ORIGINS + CONFIGURED_FRONTEND_ORIGINS))

app = FastAPI(title="Location API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-Admin-Key"],
)


class LocationCreate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class LocationRecord(LocationCreate):
    id: int
    created_at: datetime


class Headline(BaseModel):
    title: str
    source: str
    url: str
    published_at: datetime


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


initialize_database()


@app.on_event("startup")
def startup() -> None:
    initialize_database()


def require_admin_key(x_admin_key: str | None = Header(default=None)) -> None:
    if not ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The admin API is not configured.",
        )
    if x_admin_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid admin API key is required.",
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Location API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.post("/api/locations", response_model=LocationRecord, status_code=status.HTTP_201_CREATED)
def create_location(location: LocationCreate) -> LocationRecord:
    created_at = datetime.now(timezone.utc)
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO locations (latitude, longitude, created_at) VALUES (?, ?, ?)",
            (location.latitude, location.longitude, created_at.isoformat()),
        )
        location_id = cursor.lastrowid

    return LocationRecord(
        id=location_id,
        latitude=location.latitude,
        longitude=location.longitude,
        created_at=created_at,
    )


@app.get("/api/locations", response_model=list[LocationRecord], dependencies=[Depends(require_admin_key)])
def list_locations(limit: int = Query(default=100, ge=1, le=500)) -> list[LocationRecord]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, latitude, longitude, created_at FROM locations ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()

    return [LocationRecord(**dict(row)) for row in rows]


@app.delete("/api/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin_key)])
def delete_location(location_id: int) -> None:
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM locations WHERE id = ?", (location_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found.")


@app.get("/api/headlines", response_model=list[Headline])
def list_headlines() -> list[Headline]:
    configured_headlines = os.getenv("HEADLINES_JSON", "[]")
    try:
        headlines = json.loads(configured_headlines)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=500, detail="HEADLINES_JSON is not valid JSON.") from error

    if not isinstance(headlines, list):
        raise HTTPException(status_code=500, detail="HEADLINES_JSON must contain a list.")

    return [Headline(**headline) for headline in headlines[:10]]
