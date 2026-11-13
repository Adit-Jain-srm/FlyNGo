"""FastAPI application entrypoint for FlyNGo backend."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import sqlite3

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import CORS_ORIGINS
from backend.app.db.connection import get_connection, get_db
from backend.app.db.init import init_db
from backend.app.db.refdata_loader import load_reference_data
from backend.app.db.seed import seed_open_requests
from backend.app.errors import register_exception_handlers
from backend.app.log import configure_logging, get_logger
from backend.app.schemas import HealthResponse

configure_logging()
logger = get_logger()

_STARTUP_TABLES = (
    "airports",
    "flights",
    "hotels",
    "routes",
    "suppliers",
    "vehicles",
    "booked_rides",
    "ride_requests",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup lifecycle: initialize schema, load ref data, seed open requests."""
    conn = get_connection()
    try:
        # Schema and the three seeded requests are small. The flight catalog
        # is not: one remote statement per row would hold the first request.
        init_db(conn)
        if not _catalog_loaded(conn):
            load_reference_data(conn)
        seed_open_requests(conn)
        counts = _active_counts(conn)
        logger.info(
            "startup complete %s",
            " ".join(f"{name}={counts[name]}" for name in _STARTUP_TABLES),
        )
    except Exception:
        logger.exception("startup failed")
        raise
    finally:
        conn.close()
    yield


app = FastAPI(
    title="FlyNGo API",
    description="Backend API for FlyNGo Airport Taxi Ride Offers Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom exception handlers
register_exception_handlers(app)

# Include routers
from backend.app.routers import bookings, catalog, changes, offers, requests, suppliers

app.include_router(catalog.router)
app.include_router(requests.router)
app.include_router(suppliers.router)
app.include_router(offers.router)
app.include_router(bookings.router)
app.include_router(changes.router)


@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Service health check and database table counts",
)
def get_health(conn: sqlite3.Connection = Depends(get_db)) -> HealthResponse:
    """Return health status and current active record counts for key tables."""
    return HealthResponse(status="healthy", counts=_active_counts(conn))


def _catalog_loaded(conn: sqlite3.Connection) -> bool:
    """True when the hosted catalog is already present, so startup can skip the reload."""
    try:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM flights WHERE is_active = 1").fetchone()
    except Exception:
        return False
    if row is None:
        return False
    count = row["cnt"] if not isinstance(row, tuple) else row[0]
    return int(count) >= 100


def _active_counts(conn: sqlite3.Connection) -> dict[str, int]:
    """Count active rows in the tables reported at startup and on /api/health."""
    counts: dict[str, int] = {}
    cur = conn.cursor()
    for tbl in _STARTUP_TABLES:
        row = cur.execute(f"SELECT COUNT(*) AS cnt FROM {tbl} WHERE is_active = 1;").fetchone()
        counts[tbl] = row["cnt"] if row else 0
    return counts
