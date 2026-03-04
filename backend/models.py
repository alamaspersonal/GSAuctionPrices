"""
Pydantic models for the GSAuctionPrices API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


# ── Response Models ─────────────────────────────────────────────────

class AuctionEntry(BaseModel):
    """A single normalised auction lot entry."""
    id: str
    report_date: Optional[str] = None
    published_date: Optional[str] = None

    # Market
    market_name: Optional[str] = None
    market_city: Optional[str] = None
    market_state: Optional[str] = None
    slug_id: Optional[int] = None
    report_title: Optional[str] = None
    market_type: Optional[str] = None
    is_summary: bool = False

    # Animal
    species: Optional[str] = None
    commodity: Optional[str] = None
    animal_class: Optional[str] = None
    breed_type: Optional[str] = None
    quality_grade: Optional[str] = None
    lot_desc: Optional[str] = None
    dressing: Optional[str] = None
    age: Optional[str] = None
    frame: Optional[str] = None
    muscle_grade: Optional[str] = None
    yield_grade: Optional[str] = None

    # Pricing
    price_unit: Optional[str] = None
    avg_price: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    price_per_lb: Optional[float] = None
    price_per_head: Optional[float] = None
    price_per_cwt: Optional[float] = None

    # Weight
    avg_weight: Optional[int] = None
    weight_min: Optional[int] = None
    weight_max: Optional[int] = None
    weight_break_low: Optional[int] = None
    weight_break_high: Optional[int] = None

    # Volume
    head_count: Optional[int] = None
    receipts: Optional[int] = None
    receipts_week_ago: Optional[int] = None
    receipts_year_ago: Optional[int] = None

    # Derived
    buyer_intent: Optional[str] = None

    # Narrative
    narrative: Optional[str] = None


class PaginatedEntries(BaseModel):
    """Paginated response wrapper for auction entries."""
    results: List[AuctionEntry]
    count: int
    page: int
    limit: int
    total_pages: int
    suggestions: Optional[dict] = None


class SummaryWidget(BaseModel):
    """A single at-a-glance summary widget."""
    label: str
    value: str
    sub_label: Optional[str] = None
    trend_pct: Optional[float] = None
    trend_direction: Optional[str] = None  # "up", "down", "flat"


class SummaryResponse(BaseModel):
    """At-a-glance dashboard summary."""
    widgets: List[SummaryWidget]
    total_lots: int
    total_markets: int
    total_states: int
    data_freshness: Optional[str] = None


class MarketComparison(BaseModel):
    """A row in the seller's market comparison table."""
    market_name: str
    market_state: str
    avg_price_per_lb: Optional[float] = None
    avg_price_per_head: Optional[float] = None
    lot_count: int = 0
    head_count: int = 0
    trend_pct: Optional[float] = None
    trend_direction: Optional[str] = None


class TrendPoint(BaseModel):
    """A single data point on the trend line."""
    week_label: str
    week_start: str
    avg_price_per_lb: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    lot_count: int = 0
    head_count: int = 0


class ScatterPoint(BaseModel):
    """A single data point on the scatter plot."""
    id: str
    avg_weight: int
    price_per_lb: float
    head_count: int
    commodity: str
    species: str
    animal_class: str
    market_name: Optional[str] = None
    report_date: Optional[str] = None


class MetaClasses(BaseModel):
    """Available classes for a species+commodity combination."""
    classes: List[dict]  # [{name, count}]


class MetaMarkets(BaseModel):
    """Available markets."""
    markets: List[dict]  # [{name, state, city, count}]


class MetaStates(BaseModel):
    """Available states."""
    states: List[dict]  # [{code, count}]


class MetaGrades(BaseModel):
    """Available quality grades."""
    grades: List[dict]  # [{name, count}]


class ProfitabilityRequest(BaseModel):
    """Input for profitability calculator."""
    purchase_price_per_head: float
    purchase_weight: float
    target_sell_weight: float = 120
    feed_cost_per_lb_gain: float = 0.45
    mortality_pct: float = 3.0


class ProfitabilityResponse(BaseModel):
    """Output from profitability calculator."""
    weight_gain: float
    feed_cost_total: float
    shrink_loss: float
    total_investment: float
    break_even_per_lb: float
    break_even_per_cwt: float
    break_even_per_head: float
    current_market_avg_per_lb: Optional[float] = None
    margin_per_head: Optional[float] = None
    margin_pct: Optional[float] = None
