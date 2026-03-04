"""
Tools router — unit converter and profitability calculator.
"""

from fastapi import APIRouter
from typing import Optional
from datetime import datetime, timedelta

from ..models import ProfitabilityRequest, ProfitabilityResponse

router = APIRouter(prefix="/api/tools", tags=["Tools"])


@router.post("/profitability", response_model=ProfitabilityResponse)
async def calculate_profitability(
    req: ProfitabilityRequest,
    species: Optional[str] = None,
    animal_class: Optional[str] = None,
):
    """
    Calculate break-even and margin for a feeder operation.
    Optionally looks up current market price for the target weight class.
    """
    weight_gain = req.target_sell_weight - req.purchase_weight
    feed_cost_total = weight_gain * req.feed_cost_per_lb_gain
    shrink_loss = req.purchase_price_per_head * (req.mortality_pct / 100)
    total_investment = req.purchase_price_per_head + feed_cost_total + shrink_loss

    break_even_per_lb = total_investment / req.target_sell_weight if req.target_sell_weight > 0 else 0
    break_even_per_cwt = break_even_per_lb * 100
    break_even_per_head = total_investment

    # Try to look up current market avg for the target weight class
    current_market_avg = None
    margin_per_head = None
    margin_pct = None

    if species:
        from ..main import get_db
        conn = get_db()

        date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        where = "is_summary = 0 AND price_per_lb IS NOT NULL AND species = ? AND buyer_intent = 'meat' AND report_date >= ?"
        values = [species, date_from]

        # Look for target weight ± 15 lbs
        weight_low = req.target_sell_weight - 15
        weight_high = req.target_sell_weight + 15
        where += " AND avg_weight >= ? AND avg_weight <= ?"
        values.extend([weight_low, weight_high])

        if animal_class:
            where += " AND animal_class = ?"
            values.append(animal_class)

        row = conn.execute(
            f"""SELECT
                SUM(price_per_lb * COALESCE(head_count,1)) / NULLIF(SUM(COALESCE(head_count,1)), 0) as avg_ppl
            FROM auction_entries WHERE {where}""",
            values
        ).fetchone()

        if row and row["avg_ppl"]:
            current_market_avg = round(row["avg_ppl"], 4)
            sell_revenue = current_market_avg * req.target_sell_weight
            margin_per_head = round(sell_revenue - total_investment, 2)
            margin_pct = round(margin_per_head / total_investment * 100, 2) if total_investment > 0 else None

    return ProfitabilityResponse(
        weight_gain=round(weight_gain, 2),
        feed_cost_total=round(feed_cost_total, 2),
        shrink_loss=round(shrink_loss, 2),
        total_investment=round(total_investment, 2),
        break_even_per_lb=round(break_even_per_lb, 4),
        break_even_per_cwt=round(break_even_per_cwt, 2),
        break_even_per_head=round(break_even_per_head, 2),
        current_market_avg_per_lb=current_market_avg,
        margin_per_head=margin_per_head,
        margin_pct=margin_pct,
    )
