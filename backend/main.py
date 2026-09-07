from datetime import datetime, timezone
import json
from pathlib import Path
import os
import sqlite3
from email.utils import parsedate_to_datetime
from urllib.parse import quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ElementTree

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
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    client_id: str = Field(min_length=1, max_length=100)
    status: str = Field(default="allowed", pattern="^(allowed|not_allowed)$")


class LocationRecord(BaseModel):
    latitude: float | None
    longitude: float | None
    id: int
    created_at: datetime
    status: str


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
        columns = connection.execute("PRAGMA table_info(locations)").fetchall()
        if columns and not any(column[1] == "client_id" for column in columns):
            connection.execute("ALTER TABLE locations ADD COLUMN client_id TEXT")
        if columns and not any(column[1] == "status" for column in columns):
            connection.execute("ALTER TABLE locations ADD COLUMN status TEXT NOT NULL DEFAULT 'allowed'")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                created_at TEXT NOT NULL,
                client_id TEXT,
                status TEXT NOT NULL DEFAULT 'allowed'
            )
            """
        )
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_locations_client_id "
            "ON locations(client_id) WHERE client_id IS NOT NULL"
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


@app.post("/api/locations", response_model=LocationRecord)
def create_location(location: LocationCreate) -> LocationRecord:
    created_at = datetime.now(timezone.utc)
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM locations WHERE client_id = ?", (location.client_id,)
        ).fetchone()
        if existing:
            location_id = existing[0]
            connection.execute(
                "UPDATE locations SET latitude = ?, longitude = ?, created_at = ?, status = ? WHERE id = ?",
                (location.latitude or 0, location.longitude or 0, created_at.isoformat(), location.status, location_id),
            )
        else:
            cursor = connection.execute(
                "INSERT INTO locations (latitude, longitude, created_at, client_id, status) VALUES (?, ?, ?, ?, ?)",
                (location.latitude or 0, location.longitude or 0, created_at.isoformat(), location.client_id, location.status),
            )
            location_id = cursor.lastrowid

    return LocationRecord(
        id=location_id,
        latitude=location.latitude if location.status == "allowed" else None,
        longitude=location.longitude if location.status == "allowed" else None,
        created_at=created_at,
        status=location.status,
    )


@app.get("/api/locations", response_model=list[LocationRecord], dependencies=[Depends(require_admin_key)])
def list_locations(limit: int = Query(default=100, ge=1, le=500)) -> list[LocationRecord]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, latitude, longitude, created_at, status FROM locations ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()

    records = []
    for row in rows:
        record = dict(row)
        if record["status"] != "allowed":
            record["latitude"] = None
            record["longitude"] = None
        records.append(LocationRecord(**record))
    return records


@app.delete("/api/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin_key)])
def delete_location(location_id: int) -> None:
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM locations WHERE id = ?", (location_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found.")


def configured_headlines() -> list[Headline]:
    configured_headlines = os.getenv("HEADLINES_JSON", "[]")
    try:
        headlines = json.loads(configured_headlines)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=500, detail="HEADLINES_JSON is not valid JSON.") from error

    if not isinstance(headlines, list):
        raise HTTPException(status_code=500, detail="HEADLINES_JSON must contain a list.")

    return [Headline(**headline) for headline in headlines[:10]]


def local_news_headlines(latitude: float, longitude: float) -> list[Headline]:
    headers = {"User-Agent": "LocationNews/1.0 (location app)"}
    reverse_url = (
        "https://nominatim.openstreetmap.org/reverse?format=jsonv2&zoom=10"
        f"&lat={latitude}&lon={longitude}"
    )
    with urlopen(Request(reverse_url, headers=headers), timeout=8) as response:
        address = json.loads(response.read().decode("utf-8")).get("address", {})

    locality = (
        address.get("city")
        or address.get("town")
        or address.get("municipality")
        or address.get("county")
        or address.get("state")
    )
    if not locality:
        return []

    news_url = f"https://news.google.com/rss/search?q={quote(locality)}&hl=en-IN&gl=IN&ceid=IN:en"
    with urlopen(Request(news_url, headers=headers), timeout=8) as response:
        root = ElementTree.fromstring(response.read())

    headlines = []
    for item in root.findall("./channel/item")[:10]:
        title = item.findtext("title")
        url = item.findtext("link")
        published = item.findtext("pubDate")
        if not title or not url or not published:
            continue
        source = item.findtext("source") or locality
        published_at = parsedate_to_datetime(published).astimezone(timezone.utc)
        headlines.append(Headline(title=title, source=source, url=url, published_at=published_at))
    return headlines


@app.get("/api/headlines", response_model=list[Headline])
def list_headlines(latitude: float | None = Query(default=None, ge=-90, le=90), longitude: float | None = Query(default=None, ge=-180, le=180)) -> list[Headline]:
    if latitude is not None and longitude is not None:
        try:
            headlines = local_news_headlines(latitude, longitude)
            if headlines:
                return headlines
        except (ElementTree.ParseError, OSError, ValueError, KeyError, TypeError):
            pass
    return configured_headlines()
