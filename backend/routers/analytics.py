"""
Analytics router — summary widgets, trend lines, scatter data, market comparison.
"""

from fastapi import APIRouter, Query
from typing import Optional, List
import sqlite3
from datetime import datetime, timedelta

from ..models import (
    SummaryResponse, SummaryWidget,
    MarketComparison, TrendPoint, ScatterPoint,
    MetaClasses, MetaMarkets, MetaStates, MetaGrades,
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """At-a-Glance dashboard summary widgets."""
    from ..main import get_db
    conn = get_db()

    # Default date window: last 14 days
    if not date_from:
        date_from = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")

    base_where = "is_summary = 0 AND avg_price IS NOT NULL AND report_date >= ?"
    base_values = [date_from]
    if date_to:
        base_where += " AND report_date <= ?"
        base_values.append(date_to)

    widgets = []

    # Goat avg price/lb
    for species, emoji in [("Goats", "🐐"), ("Sheep", "🐑")]:
        row = conn.execute(
            f"""SELECT
                SUM(CASE WHEN price_per_lb IS NOT NULL THEN price_per_lb * COALESCE(head_count, 1) ELSE 0 END)
                    / NULLIF(SUM(CASE WHEN price_per_lb IS NOT NULL THEN COALESCE(head_count, 1) ELSE 0 END), 0)
                    as weighted_avg,
                COUNT(*) as cnt
            FROM auction_entries
            WHERE {base_where} AND species = ? AND buyer_intent = 'meat'""",
            base_values + [species]
        ).fetchone()

        avg = row["weighted_avg"]
        if avg:
            widgets.append(SummaryWidget(
                label=f"{emoji} {species}",
                value=f"${avg:.2f}/lb",
                sub_label="Slaughter Avg",
                trend_pct=None,
                trend_direction=None,
            ))

    # Total volume
    row = conn.execute(
        f"SELECT COUNT(*) as lots, COUNT(DISTINCT market_name) as markets, COUNT(DISTINCT market_state) as states FROM auction_entries WHERE {base_where}",
        base_values
    ).fetchone()

    widgets.append(SummaryWidget(
        label="📊 Volume",
        value=f"{row['lots']:,} lots",
        sub_label=f"{row['markets']} markets · {row['states']} states",
    ))

    # Top gainer: compare this period vs previous period avg for each class
    period_days = 14
    prev_from = (datetime.strptime(date_from, "%Y-%m-%d") - timedelta(days=period_days)).strftime("%Y-%m-%d")
    prev_to = date_from

    gainers = conn.execute(
        f"""SELECT
            curr.species, curr.animal_class,
            curr.avg_ppl as curr_avg,
            prev.avg_ppl as prev_avg,
            CASE WHEN prev.avg_ppl > 0 THEN ((curr.avg_ppl - prev.avg_ppl) / prev.avg_ppl * 100) ELSE NULL END as change_pct
        FROM (
            SELECT species, animal_class,
                SUM(price_per_lb * COALESCE(head_count,1)) / NULLIF(SUM(COALESCE(head_count,1)), 0) as avg_ppl
            FROM auction_entries
            WHERE is_summary = 0 AND price_per_lb IS NOT NULL AND report_date >= ? AND report_date <= COALESCE(?, date('now'))
            GROUP BY species, animal_class
            HAVING COUNT(*) >= 5
        ) curr
        JOIN (
            SELECT species, animal_class,
                SUM(price_per_lb * COALESCE(head_count,1)) / NULLIF(SUM(COALESCE(head_count,1)), 0) as avg_ppl
            FROM auction_entries
            WHERE is_summary = 0 AND price_per_lb IS NOT NULL AND report_date >= ? AND report_date < ?
            GROUP BY species, animal_class
            HAVING COUNT(*) >= 5
        ) prev ON curr.species = prev.species AND curr.animal_class = prev.animal_class
        WHERE change_pct IS NOT NULL
        ORDER BY change_pct DESC
        LIMIT 1""",
        [date_from, date_to, prev_from, prev_to]
    ).fetchone()

    if gainers:
        direction = "up" if gainers["change_pct"] > 0 else "down" if gainers["change_pct"] < 0 else "flat"
        widgets.append(SummaryWidget(
            label="🔥 Top Mover",
            value=f"{gainers['animal_class']}",
            sub_label=f"{gainers['species']}",
            trend_pct=round(gainers["change_pct"], 1),
            trend_direction=direction,
        ))

    return SummaryResponse(
        widgets=widgets,
        total_lots=row["lots"],
        total_markets=row["markets"],
        total_states=row["states"],
        data_freshness=conn.execute("SELECT MAX(published_date) as latest FROM auction_entries").fetchone()["latest"],
    )


@router.get("/compare", response_model=List[MarketComparison])
async def compare_markets(
    species: str,
    animal_class: Optional[str] = None,
    weight_min: Optional[int] = None,
    weight_max: Optional[int] = None,
    period: int = Query(30, ge=7, le=365),
):
    """Seller mode: compare avg prices across markets for a given animal profile."""
    from ..main import get_db
    conn = get_db()

    date_from = (datetime.now() - timedelta(days=period)).strftime("%Y-%m-%d")

    where = "is_summary = 0 AND price_per_lb IS NOT NULL AND species = ? AND report_date >= ?"
    values: list = [species, date_from]

    if animal_class:
        where += " AND animal_class = ?"
        values.append(animal_class)
    if weight_min is not None:
        where += " AND avg_weight >= ?"
        values.append(weight_min)
    if weight_max is not None:
        where += " AND avg_weight <= ?"
        values.append(weight_max)

    rows = conn.execute(
        f"""SELECT
            market_name, market_state,
            SUM(price_per_lb * COALESCE(head_count,1)) / NULLIF(SUM(COALESCE(head_count,1)), 0) as avg_ppl,
            SUM(COALESCE(price_per_head, 0) * COALESCE(head_count,1)) / NULLIF(SUM(CASE WHEN price_per_head IS NOT NULL THEN COALESCE(head_count,1) ELSE 0 END), 0) as avg_pph,
            COUNT(*) as lot_count,
            SUM(COALESCE(head_count, 0)) as total_head
        FROM auction_entries
        WHERE {where}
        GROUP BY market_name, market_state
        HAVING COUNT(*) >= 2
        ORDER BY avg_ppl DESC""",
        values
    ).fetchall()

    results = []
    for r in rows:
        results.append(MarketComparison(
            market_name=r["market_name"],
            market_state=r["market_state"],
            avg_price_per_lb=round(r["avg_ppl"], 4) if r["avg_ppl"] else None,
            avg_price_per_head=round(r["avg_pph"], 2) if r["avg_pph"] else None,
            lot_count=r["lot_count"],
            head_count=r["total_head"] or 0,
        ))

    return results


@router.get("/trends", response_model=List[TrendPoint])
async def get_trends(
    species: Optional[str] = None,
    commodity: Optional[str] = None,
    animal_class: Optional[str] = None,
    weight_min: Optional[int] = None,
    weight_max: Optional[int] = None,
    period: int = Query(90, ge=14, le=365),
    market: Optional[str] = None,
):
    """Weekly price trend line for a given set of filters."""
    from ..main import get_db
    conn = get_db()

    date_from = (datetime.now() - timedelta(days=period)).strftime("%Y-%m-%d")

    where = "is_summary = 0 AND price_per_lb IS NOT NULL AND report_date >= ?"
    values: list = [date_from]

    if species:
        where += " AND species = ?"
        values.append(species)
    if commodity:
        where += " AND commodity = ?"
        values.append(commodity)
    if animal_class:
        where += " AND animal_class = ?"
        values.append(animal_class)
    if weight_min is not None:
        where += " AND avg_weight >= ?"
        values.append(weight_min)
    if weight_max is not None:
        where += " AND avg_weight <= ?"
        values.append(weight_max)
    if market:
        where += " AND market_name = ?"
        values.append(market)

    # Group by ISO week
    rows = conn.execute(
        f"""SELECT
            strftime('%Y-W%W', report_date) as week_label,
            MIN(report_date) as week_start,
            SUM(price_per_lb * COALESCE(head_count,1)) / NULLIF(SUM(COALESCE(head_count,1)), 0) as avg_ppl,
            MIN(price_per_lb) as min_ppl,
            MAX(price_per_lb) as max_ppl,
            COUNT(*) as lot_count,
            SUM(COALESCE(head_count, 0)) as total_head
        FROM auction_entries
        WHERE {where}
        GROUP BY week_label
        ORDER BY week_label ASC""",
        values
    ).fetchall()

    return [
        TrendPoint(
            week_label=r["week_label"],
            week_start=r["week_start"],
            avg_price_per_lb=round(r["avg_ppl"], 4) if r["avg_ppl"] else None,
            price_min=round(r["min_ppl"], 4) if r["min_ppl"] else None,
            price_max=round(r["max_ppl"], 4) if r["max_ppl"] else None,
            lot_count=r["lot_count"],
            head_count=r["total_head"] or 0,
        )
        for r in rows
    ]


@router.get("/scatter", response_model=List[ScatterPoint])
async def get_scatter(
    species: Optional[str] = None,
    commodity: Optional[str] = None,
    date_from: Optional[str] = None,
    limit: int = Query(500, ge=10, le=2000),
):
    """Price vs Weight scatter plot data."""
    from ..main import get_db
    conn = get_db()

    where = "is_summary = 0 AND price_per_lb IS NOT NULL AND avg_weight IS NOT NULL AND avg_weight > 0"
    values: list = []

    if species:
        where += " AND species = ?"
        values.append(species)
    if commodity:
        where += " AND commodity = ?"
        values.append(commodity)
    if date_from:
        where += " AND report_date >= ?"
        values.append(date_from)

    rows = conn.execute(
        f"""SELECT id, avg_weight, price_per_lb, COALESCE(head_count, 1) as head_count,
            commodity, species, animal_class, market_name, report_date
        FROM auction_entries
        WHERE {where}
        ORDER BY report_date DESC
        LIMIT ?""",
        values + [limit]
    ).fetchall()

    return [
        ScatterPoint(
            id=r["id"],
            avg_weight=r["avg_weight"],
            price_per_lb=round(r["price_per_lb"], 4),
            head_count=r["head_count"],
            commodity=r["commodity"] or "",
            species=r["species"] or "",
            animal_class=r["animal_class"] or "",
            market_name=r["market_name"],
            report_date=r["report_date"],
        )
        for r in rows
    ]


# ── Meta endpoints for filter dropdowns ─────────────────────────────

@router.get("/meta/classes", response_model=MetaClasses)
async def get_classes(
    species: Optional[str] = None,
    intent: Optional[str] = None,
):
    """Available classes for a species + intent combo, with counts."""
    from ..main import get_db
    conn = get_db()

    where = "is_summary = 0 AND animal_class IS NOT NULL"
    values: list = []
    if species:
        where += " AND species = ?"
        values.append(species)
    if intent:
        where += " AND buyer_intent = ?"
        values.append(intent)

    rows = conn.execute(
        f"SELECT animal_class, COUNT(*) as cnt FROM auction_entries WHERE {where} GROUP BY animal_class ORDER BY cnt DESC",
        values,
    ).fetchall()
    return MetaClasses(classes=[{"name": r["animal_class"], "count": r["cnt"]} for r in rows])


@router.get("/meta/markets", response_model=MetaMarkets)
async def get_markets():
    from ..main import get_db
    conn = get_db()
    rows = conn.execute(
        "SELECT market_name, market_state, market_city, COUNT(*) as cnt FROM auction_entries WHERE is_summary = 0 GROUP BY market_name ORDER BY cnt DESC"
    ).fetchall()
    return MetaMarkets(markets=[{"name": r["market_name"], "state": r["market_state"], "city": r["market_city"], "count": r["cnt"]} for r in rows])


@router.get("/meta/states", response_model=MetaStates)
async def get_states():
    from ..main import get_db
    conn = get_db()
    rows = conn.execute(
        "SELECT market_state, COUNT(*) as cnt FROM auction_entries WHERE is_summary = 0 GROUP BY market_state ORDER BY cnt DESC"
    ).fetchall()
    return MetaStates(states=[{"code": r["market_state"], "count": r["cnt"]} for r in rows])


@router.get("/meta/grades", response_model=MetaGrades)
async def get_grades():
    from ..main import get_db
    conn = get_db()
    rows = conn.execute(
        "SELECT quality_grade, COUNT(*) as cnt FROM auction_entries WHERE is_summary = 0 AND quality_grade IS NOT NULL GROUP BY quality_grade ORDER BY cnt DESC"
    ).fetchall()
    return MetaGrades(grades=[{"name": r["quality_grade"], "count": r["cnt"]} for r in rows])
