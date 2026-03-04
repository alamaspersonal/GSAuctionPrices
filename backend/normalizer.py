"""
LMPR Data Normalizer

Reads raw LMPR CSV files from ../lmpr_data/ and produces a list of
normalised AuctionEntry dicts with:
  - column alias resolution
  - type coercion
  - derived fields (price_per_lb, price_per_head, buyer_intent, breed_type)
"""

import os
import glob
import re
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "lmpr_data")

# ── Column alias map ────────────────────────────────────────────────
# Some slug reports (2922, 3454, 2907) use different column names.
ALIAS_MAP: Dict[str, str] = {
    "wtd_Avg_Price": "avg_price",
    "wtd_avg_wt": "avg_weight",
    "published_Date": "published_date",
    "weight_Break_Low": "weight_break_low",
    "weight_Break_High": "weight_break_high",
    "weight_Collect": "weight_collect",
    "muscle_Grade": "muscle_grade",
    "price_min": "avg_price_min",
    "price_max": "avg_price_max",
    "weight_min": "avg_weight_min",
    "weight_max": "avg_weight_max",
    "previous_Report_Date": "previous_report_date",
    "pO_Pct": "po_pct",
    "pO_pct_previous": "po_pct_previous",
}

# ── Commodity → buyer intent mapping ────────────────────────────────
INTENT_MAP: Dict[str, str] = {
    "Slaughter Goats": "meat",
    "Slaughter Sheep/Lambs": "meat",
    "Feeder Goats": "feeder",
    "Feeder Sheep/Lambs": "feeder",
    "Replacement Goats": "breeding",
    "Replacement Sheep/Lambs": "breeding",
}

# ── Class → breed type mapping ──────────────────────────────────────
HAIR_CLASSES = {
    "Hair Breeds", "Hair Ewes", "Hair Bucks", "Hair Lambs",
}
WOOLED_CLASSES = {
    "Wooled & Shorn", "Wooled", "Shorn",
}

# Rows with these class values are data anomalies
EXCLUDED_CLASSES = {"Hogs", "Sheep"}


def _resolve_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """Rename aliased columns to their canonical names."""
    rename = {k: v for k, v in ALIAS_MAP.items() if k in df.columns}
    return df.rename(columns=rename)


def _normalize_date(val: Any) -> str | None:
    """Convert MM/DD/YYYY or MM/DD/YYYY HH:MM:SS to ISO format."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    s = str(val).strip()
    if not s:
        return None
    # Try MM/DD/YYYY HH:MM:SS
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            if fmt == "%m/%d/%Y %H:%M:%S":
                return dt.strftime("%Y-%m-%dT%H:%M:%S")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return s  # Return as-is if unparseable


def _coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce columns to the correct types."""
    float_cols = [
        "avg_price", "avg_price_min", "avg_price_max",
    ]
    int_cols = [
        "avg_weight", "avg_weight_min", "avg_weight_max",
        "weight_break_low", "weight_break_high",
        "head_count", "receipts", "receipts_week_ago", "receipts_year_ago",
    ]
    for c in float_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in int_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
            df[c] = df[c].where(df[c].notna(), None)
    return df


def _derive_breed_type(cls: Any) -> str | None:
    if pd.isna(cls):
        return None
    if cls in HAIR_CLASSES:
        return "Hair"
    if cls in WOOLED_CLASSES:
        return "Wooled"
    return None


def _derive_prices(row: pd.Series) -> Dict[str, float | None]:
    """Compute price_per_lb, price_per_head, price_per_cwt from reported data."""
    price = row.get("avg_price")
    unit = row.get("price_unit")
    weight = row.get("avg_weight")

    if pd.isna(price) or price is None:
        return {"price_per_lb": None, "price_per_head": None, "price_per_cwt": None}

    price = float(price)

    if unit == "Per Cwt":
        per_lb = round(price / 100, 4)
        per_head = round(per_lb * float(weight), 2) if weight and not pd.isna(weight) and float(weight) > 0 else None
        return {"price_per_lb": per_lb, "price_per_head": per_head, "price_per_cwt": price}

    if unit == "Per Unit":
        per_head = price
        if weight and not pd.isna(weight) and float(weight) > 0:
            per_lb = round(price / float(weight), 4)
            per_cwt = round(per_lb * 100, 2)
        else:
            per_lb = None
            per_cwt = None
        return {"price_per_lb": per_lb, "price_per_head": per_head, "price_per_cwt": per_cwt}

    return {"price_per_lb": None, "price_per_head": None, "price_per_cwt": None}


def _row_to_entry(row: pd.Series, row_idx: int) -> Dict[str, Any] | None:
    """Convert a single DataFrame row into a normalised dict."""
    # Skip non-detail rows
    section = row.get("_section", "")
    if section == "Report Header":
        return None

    # Skip anomalous classes
    cls = row.get("class")
    if pd.notna(cls) and cls in EXCLUDED_CLASSES:
        return None

    # Skip rows without price data
    if pd.isna(row.get("avg_price")):
        return None

    slug = row.get("slug_id")
    report_date = row.get("report_date", "")
    entry_id = f"{slug}-{str(report_date).replace('/', '-')}-{row_idx:04d}"

    prices = _derive_prices(row)
    commodity = row.get("commodity")

    def safe_float(v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    def safe_int(v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return None
        try:
            return int(float(v))
        except (ValueError, TypeError):
            return None

    def safe_str(v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return None
        return str(v).strip() if str(v).strip() else None

    market_type_cat = safe_str(row.get("market_type_category"))
    is_summary = market_type_cat == "Summary"

    return {
        "id": entry_id,
        "report_date": _normalize_date(report_date),
        "published_date": _normalize_date(row.get("published_date")),
        # Market
        "market_name": safe_str(row.get("market_location_name")),
        "market_city": safe_str(row.get("market_location_city")),
        "market_state": safe_str(row.get("market_location_state")),
        "slug_id": safe_int(slug),
        "report_title": safe_str(row.get("report_title")),
        "market_type": safe_str(market_type_cat),
        "is_summary": is_summary,
        # Animal
        "species": safe_str(row.get("category")),
        "commodity": safe_str(commodity),
        "animal_class": safe_str(cls),
        "breed_type": _derive_breed_type(cls),
        "quality_grade": safe_str(row.get("quality_grade_name")),
        "lot_desc": safe_str(row.get("lot_desc")),
        "dressing": safe_str(row.get("dressing")),
        "age": safe_str(row.get("age")),
        "frame": safe_str(row.get("frame")),
        "muscle_grade": safe_str(row.get("muscle_grade")),
        "yield_grade": safe_str(row.get("yield_grade")),
        # Pricing
        "price_unit": safe_str(row.get("price_unit")),
        "avg_price": safe_float(row.get("avg_price")),
        "price_min": safe_float(row.get("avg_price_min")),
        "price_max": safe_float(row.get("avg_price_max")),
        "price_per_lb": prices["price_per_lb"],
        "price_per_head": prices["price_per_head"],
        "price_per_cwt": prices["price_per_cwt"],
        # Weight
        "avg_weight": safe_int(row.get("avg_weight")),
        "weight_min": safe_int(row.get("avg_weight_min")),
        "weight_max": safe_int(row.get("avg_weight_max")),
        "weight_break_low": safe_int(row.get("weight_break_low")),
        "weight_break_high": safe_int(row.get("weight_break_high")),
        # Volume
        "head_count": safe_int(row.get("head_count")),
        "receipts": safe_int(row.get("receipts")),
        "receipts_week_ago": safe_int(row.get("receipts_week_ago")),
        "receipts_year_ago": safe_int(row.get("receipts_year_ago")),
        # Derived
        "buyer_intent": INTENT_MAP.get(commodity) if pd.notna(commodity) else None,
        # Narrative
        "narrative": safe_str(row.get("report_narrative")),
    }


def load_and_normalize(data_dir: str | None = None) -> List[Dict[str, Any]]:
    """Load all LMPR CSVs and return a list of normalised entry dicts."""
    directory = data_dir or DATA_DIR
    files = sorted(glob.glob(os.path.join(directory, "lmpr_*.csv")))

    if not files:
        raise FileNotFoundError(f"No CSV files found in {directory}")

    all_entries: List[Dict[str, Any]] = []

    for filepath in files:
        df = pd.read_csv(filepath, low_memory=False)
        df = _resolve_aliases(df)
        df = _coerce_types(df)

        for idx, row in df.iterrows():
            entry = _row_to_entry(row, int(idx))
            if entry is not None:
                all_entries.append(entry)

    return all_entries


if __name__ == "__main__":
    entries = load_and_normalize()
    print(f"Normalised {len(entries)} entries from {DATA_DIR}")
    if entries:
        import json
        print(json.dumps(entries[0], indent=2, default=str))
