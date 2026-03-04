"""
Entries router — filtered lot listing with pagination.
"""

from fastapi import APIRouter, Query, Depends
from typing import Optional, List
import sqlite3
import math

from ..models import AuctionEntry, PaginatedEntries

router = APIRouter(prefix="/api/entries", tags=["Entries"])


def _build_where(params: dict) -> tuple[str, list]:
    """Build a WHERE clause from filter parameters."""
    clauses = []
    values = []

    if params.get("species"):
        clauses.append("species = ?")
        values.append(params["species"])

    if params.get("intent"):
        clauses.append("buyer_intent = ?")
        values.append(params["intent"])

    if params.get("commodity"):
        clauses.append("commodity = ?")
        values.append(params["commodity"])

    if params.get("animal_class"):
        classes = params["animal_class"].split(",")
        placeholders = ",".join(["?" for _ in classes])
        clauses.append(f"animal_class IN ({placeholders})")
        values.extend(classes)

    if params.get("breed_type"):
        clauses.append("breed_type = ?")
        values.append(params["breed_type"])

    if params.get("grade"):
        grades = params["grade"].split(",")
        placeholders = ",".join(["?" for _ in grades])
        clauses.append(f"quality_grade IN ({placeholders})")
        values.extend(grades)

    if params.get("weight_min") is not None:
        clauses.append("avg_weight >= ?")
        values.append(params["weight_min"])

    if params.get("weight_max") is not None:
        clauses.append("avg_weight <= ?")
        values.append(params["weight_max"])

    if params.get("price_min") is not None:
        clauses.append("price_per_lb >= ?")
        values.append(params["price_min"])

    if params.get("price_max") is not None:
        clauses.append("price_per_lb <= ?")
        values.append(params["price_max"])

    if params.get("state"):
        states = params["state"].split(",")
        placeholders = ",".join(["?" for _ in states])
        clauses.append(f"market_state IN ({placeholders})")
        values.extend(states)

    if params.get("market"):
        clauses.append("market_name = ?")
        values.append(params["market"])

    if params.get("lot_desc"):
        clauses.append("lot_desc = ?")
        values.append(params["lot_desc"])

    if params.get("date_from"):
        clauses.append("report_date >= ?")
        values.append(params["date_from"])

    if params.get("date_to"):
        clauses.append("report_date <= ?")
        values.append(params["date_to"])

    if not params.get("include_summary"):
        clauses.append("is_summary = 0")

    # Always require avg_price to be non-null
    clauses.append("avg_price IS NOT NULL")

    where = " AND ".join(clauses) if clauses else "1=1"
    return where, values


SORT_MAP = {
    "price_per_lb": "price_per_lb",
    "price_per_head": "price_per_head",
    "avg_weight": "avg_weight",
    "head_count": "head_count",
    "report_date": "report_date",
    "avg_price": "avg_price",
}


@router.get("", response_model=PaginatedEntries)
async def list_entries(
    species: Optional[str] = None,
    intent: Optional[str] = None,
    commodity: Optional[str] = None,
    animal_class: Optional[str] = None,
    breed_type: Optional[str] = None,
    grade: Optional[str] = None,
    weight_min: Optional[int] = None,
    weight_max: Optional[int] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    state: Optional[str] = None,
    market: Optional[str] = None,
    lot_desc: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    include_summary: bool = False,
    sort_by: str = "report_date",
    sort_dir: str = "desc",
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    """List auction entries with filters, sorting, and pagination."""
    from ..main import get_db

    params = {
        "species": species, "intent": intent, "commodity": commodity,
        "animal_class": animal_class, "breed_type": breed_type, "grade": grade,
        "weight_min": weight_min, "weight_max": weight_max,
        "price_min": price_min, "price_max": price_max,
        "state": state, "market": market, "lot_desc": lot_desc,
        "date_from": date_from, "date_to": date_to,
        "include_summary": include_summary,
    }

    where, values = _build_where(params)

    sort_col = SORT_MAP.get(sort_by, "report_date")
    sort_direction = "ASC" if sort_dir.lower() == "asc" else "DESC"

    conn = get_db()

    # Count
    count_row = conn.execute(f"SELECT COUNT(*) as cnt FROM auction_entries WHERE {where}", values).fetchone()
    total = count_row["cnt"]

    # Paginate
    offset = (page - 1) * limit
    rows = conn.execute(
        f"SELECT * FROM auction_entries WHERE {where} ORDER BY {sort_col} {sort_direction} LIMIT ? OFFSET ?",
        values + [limit, offset]
    ).fetchall()

    entries = [AuctionEntry(**dict(r)) for r in rows]
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Generate suggestions if zero results
    suggestions = None
    if total == 0:
        suggestions = _generate_suggestions(conn, params)

    return PaginatedEntries(
        results=entries,
        count=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        suggestions=suggestions,
    )


@router.get("/{entry_id}", response_model=AuctionEntry)
async def get_entry(entry_id: str):
    """Get a single entry by ID."""
    from ..main import get_db
    conn = get_db()
    row = conn.execute("SELECT * FROM auction_entries WHERE id = ?", [entry_id]).fetchone()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Entry not found")
    return AuctionEntry(**dict(row))


def _generate_suggestions(conn: sqlite3.Connection, params: dict) -> dict:
    """Generate smart suggestions when zero results are found."""
    suggestions = {}

    # Try expanding weight range by ±20 lbs
    if params.get("weight_min") is not None or params.get("weight_max") is not None:
        expanded = params.copy()
        w_min = (params.get("weight_min") or 0) - 20
        w_max = (params.get("weight_max") or 350) + 20
        expanded["weight_min"] = max(0, w_min)
        expanded["weight_max"] = w_max
        where, values = _build_where(expanded)
        row = conn.execute(f"SELECT COUNT(*) as cnt FROM auction_entries WHERE {where}", values).fetchone()
        if row["cnt"] > 0:
            suggestions["weight_expanded"] = {
                "range": [expanded["weight_min"], expanded["weight_max"]],
                "count": row["cnt"],
            }

    # Try nearby states
    if params.get("state"):
        no_state = params.copy()
        no_state["state"] = None
        where, values = _build_where(no_state)
        rows = conn.execute(
            f"SELECT market_state, COUNT(*) as cnt FROM auction_entries WHERE {where} GROUP BY market_state ORDER BY cnt DESC LIMIT 5",
            values
        ).fetchall()
        if rows:
            suggestions["states_nearby"] = [{"state": r["market_state"], "count": r["cnt"]} for r in rows]

    # Try expanding time range to 30 days
    if params.get("date_from"):
        expanded = params.copy()
        expanded["date_from"] = None
        where, values = _build_where(expanded)
        row = conn.execute(f"SELECT COUNT(*) as cnt FROM auction_entries WHERE {where}", values).fetchone()
        if row["cnt"] > 0:
            suggestions["time_expanded"] = {"days": "all", "count": row["cnt"]}

    return suggestions if suggestions else None
