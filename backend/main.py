"""
GSAuctionPrices API — Main Application

FastAPI backend that serves normalised USDA LMPR livestock auction data.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

from .database import setup_database
from .routers import entries, analytics, tools

# ── Database connection (module-level singleton) ────────────────────
_db_conn: sqlite3.Connection | None = None


def get_db() -> sqlite3.Connection:
    """Return the shared database connection."""
    if _db_conn is None:
        raise RuntimeError("Database not initialised")
    return _db_conn


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    global _db_conn
    _db_conn = setup_database()
    yield
    if _db_conn:
        _db_conn.close()


# ── App ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="GSAuctionPrices API",
    description="Livestock auction price data for Sheep & Goats — normalised from USDA LMPR reports",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(entries.router)
app.include_router(analytics.router)
app.include_router(tools.router)


@app.get("/", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    conn = get_db()
    row = conn.execute("SELECT COUNT(*) as cnt FROM auction_entries").fetchone()
    return {
        "status": "ok",
        "service": "GSAuctionPrices API",
        "entries": row["cnt"],
    }
