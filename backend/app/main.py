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
from backend.app.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup lifecycle: initialize schema, load ref data, seed open requests."""
    conn = get_connection()
    try:
        init_db(conn)
        load_reference_data(conn)
        seed_open_requests(conn)
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


@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Service health check and database table counts",
)
def get_health(conn: sqlite3.Connection = Depends(get_db)) -> HealthResponse:
    """Return health status and current active record counts for key tables."""
    tables = [
        "airports",
        "flights",
        "hotels",
        "routes",
        "suppliers",
        "vehicles",
        "booked_rides",
        "ride_requests",
    ]
    counts: dict[str, int] = {}
    cur = conn.cursor()
    for tbl in tables:
        row = cur.execute(f"SELECT COUNT(*) AS cnt FROM {tbl} WHERE is_active = 1;").fetchone()
        counts[tbl] = row["cnt"] if row else 0

    return HealthResponse(status="healthy", counts=counts)
