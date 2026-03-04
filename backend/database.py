"""
Database layer for GSAuctionPrices.

Uses SQLite with a single `auction_entries` table.
On first run (or on request), the normaliser ingests all CSVs.
"""

import sqlite3
import os
import json
from typing import List, Dict, Any, Optional

from .normalizer import load_and_normalize

DB_PATH = os.path.join(os.path.dirname(__file__), "auction.db")

# ── Schema ──────────────────────────────────────────────────────────

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS auction_entries (
    id               TEXT PRIMARY KEY,
    report_date      TEXT,
    published_date   TEXT,

    market_name      TEXT,
    market_city      TEXT,
    market_state     TEXT,
    slug_id          INTEGER,
    report_title     TEXT,
    market_type      TEXT,
    is_summary       INTEGER DEFAULT 0,

    species          TEXT,
    commodity        TEXT,
    animal_class     TEXT,
    breed_type       TEXT,
    quality_grade    TEXT,
    lot_desc         TEXT,
    dressing         TEXT,
    age              TEXT,
    frame            TEXT,
    muscle_grade     TEXT,
    yield_grade      TEXT,

    price_unit       TEXT,
    avg_price        REAL,
    price_min        REAL,
    price_max        REAL,
    price_per_lb     REAL,
    price_per_head   REAL,
    price_per_cwt    REAL,

    avg_weight       INTEGER,
    weight_min       INTEGER,
    weight_max       INTEGER,
    weight_break_low  INTEGER,
    weight_break_high INTEGER,

    head_count       INTEGER,
    receipts         INTEGER,
    receipts_week_ago INTEGER,
    receipts_year_ago INTEGER,

    buyer_intent     TEXT,
    narrative        TEXT
);
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_species ON auction_entries(species);",
    "CREATE INDEX IF NOT EXISTS idx_commodity ON auction_entries(commodity);",
    "CREATE INDEX IF NOT EXISTS idx_animal_class ON auction_entries(animal_class);",
    "CREATE INDEX IF NOT EXISTS idx_buyer_intent ON auction_entries(buyer_intent);",
    "CREATE INDEX IF NOT EXISTS idx_market_state ON auction_entries(market_state);",
    "CREATE INDEX IF NOT EXISTS idx_report_date ON auction_entries(report_date);",
    "CREATE INDEX IF NOT EXISTS idx_avg_weight ON auction_entries(avg_weight);",
    "CREATE INDEX IF NOT EXISTS idx_price_per_lb ON auction_entries(price_per_lb);",
    "CREATE INDEX IF NOT EXISTS idx_breed_type ON auction_entries(breed_type);",
]

INSERT_ENTRY = """
INSERT OR REPLACE INTO auction_entries (
    id, report_date, published_date,
    market_name, market_city, market_state, slug_id, report_title, market_type, is_summary,
    species, commodity, animal_class, breed_type, quality_grade, lot_desc,
    dressing, age, frame, muscle_grade, yield_grade,
    price_unit, avg_price, price_min, price_max, price_per_lb, price_per_head, price_per_cwt,
    avg_weight, weight_min, weight_max, weight_break_low, weight_break_high,
    head_count, receipts, receipts_week_ago, receipts_year_ago,
    buyer_intent, narrative
) VALUES (
    :id, :report_date, :published_date,
    :market_name, :market_city, :market_state, :slug_id, :report_title, :market_type, :is_summary,
    :species, :commodity, :animal_class, :breed_type, :quality_grade, :lot_desc,
    :dressing, :age, :frame, :muscle_grade, :yield_grade,
    :price_unit, :avg_price, :price_min, :price_max, :price_per_lb, :price_per_head, :price_per_cwt,
    :avg_weight, :weight_min, :weight_max, :weight_break_low, :weight_break_high,
    :head_count, :receipts, :receipts_week_ago, :receipts_year_ago,
    :buyer_intent, :narrative
);
"""


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Get a SQLite connection with row_factory set."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create tables and indexes."""
    conn.execute(CREATE_TABLE)
    for idx_sql in INDEXES:
        conn.execute(idx_sql)
    conn.commit()


def ingest_data(conn: sqlite3.Connection, data_dir: str | None = None) -> int:
    """Run the normaliser and insert all entries into the DB."""
    entries = load_and_normalize(data_dir)
    cursor = conn.cursor()
    for entry in entries:
        cursor.execute(INSERT_ENTRY, entry)
    conn.commit()
    return len(entries)


def get_row_count(conn: sqlite3.Connection) -> int:
    """Return total row count."""
    row = conn.execute("SELECT COUNT(*) as cnt FROM auction_entries").fetchone()
    return row["cnt"]


def setup_database(db_path: str | None = None, data_dir: str | None = None) -> sqlite3.Connection:
    """Full setup: create DB, ingest if empty."""
    conn = get_connection(db_path)
    init_db(conn)
    count = get_row_count(conn)
    if count == 0:
        print("Database empty — ingesting LMPR data...")
        n = ingest_data(conn, data_dir)
        print(f"Ingested {n} entries.")
    else:
        print(f"Database already has {count} entries.")
    return conn
