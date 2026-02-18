"""
LMPR Data Fetcher for GSAuctionPrices

Fetches LMPR (Livestock Mandatory Price Reporting) data from the
USDA MARS API for all slug IDs defined in .env, limited to the
past 100 days.

Usage:
    python get_lmpr_data.py
"""

import requests
import pandas as pd
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()

API_KEY = os.getenv("USDA_API_KEY", "")
SLUG_IDS_RAW = os.getenv("LMPR_SLUG_IDS", "")
SLUG_IDS = [s.strip() for s in SLUG_IDS_RAW.split(",") if s.strip()]

BASE_URL = "https://marsapi.ams.usda.gov/services/v1.2/reports"
DAYS_BACK = 100
REQUEST_DELAY = 1.0  # seconds between API calls

OUTPUT_DIR = "lmpr_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def safe_request(url, params):
    """Make an authenticated GET request with throttling."""
    try:
        auth = (API_KEY, "") if API_KEY else None

        response = requests.get(
            url,
            params=params,
            auth=auth,
            timeout=60
        )
        response.raise_for_status()
        time.sleep(REQUEST_DELAY)

        try:
            data = response.json()
            if isinstance(data, str) and "Invalid slug" in data:
                return None
            return data
        except ValueError:
            return None

    except requests.exceptions.RequestException as e:
        print(f"  ✖ Request failed: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"    Response: {e.response.text[:200]}")
        return None


def flatten_sections(api_response):
    """Flatten API response sections into a single DataFrame."""
    rows = []

    if isinstance(api_response, list):
        for section in api_response:
            section_name = section.get("reportSection", "UNKNOWN")
            results = section.get("results", [])
            for r in results:
                r["_section"] = section_name
                rows.append(r)

    elif isinstance(api_response, dict):
        results = api_response.get("results", [])
        for r in results:
            r["_section"] = api_response.get("reportSection", "UNKNOWN")
            rows.append(r)

    return pd.DataFrame(rows)


# --------------------------------------------------
# Core Fetch Logic
# --------------------------------------------------

def fetch_report(slug_id, start_date, end_date):
    """Fetch data for a slug within a date range."""
    url = f"{BASE_URL}/{slug_id}"
    params = {
        "q": f"published_date={start_date}:{end_date}",
        "allSections": "true"
    }

    data = safe_request(url, params)
    if not data:
        return None
    return flatten_sections(data)


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    if not API_KEY:
        print("ERROR: USDA_API_KEY not found in .env")
        return

    if not SLUG_IDS:
        print("ERROR: LMPR_SLUG_IDS not found in .env")
        return

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=DAYS_BACK)).strftime("%Y-%m-%d")

    print(f"LMPR Data Fetcher")
    print(f"  Date range: {start_date} → {end_date} ({DAYS_BACK} days)")
    print(f"  Slug IDs:   {len(SLUG_IDS)} reports")
    print(f"  Output:     {OUTPUT_DIR}/")
    print()

    success_count = 0
    total_rows = 0

    for i, slug in enumerate(SLUG_IDS, 1):
        print(f"[{i}/{len(SLUG_IDS)}] Fetching slug {slug}...", end=" ")

        df = fetch_report(slug, start_date, end_date)

        if df is not None and not df.empty:
            out_path = os.path.join(OUTPUT_DIR, f"lmpr_{slug}.csv")
            df.to_csv(out_path, index=False)
            print(f"✔ {len(df)} rows → {out_path}")
            success_count += 1
            total_rows += len(df)
        else:
            print("✖ No data")

    print(f"\nDone. {success_count}/{len(SLUG_IDS)} reports fetched, {total_rows} total rows.")


if __name__ == "__main__":
    main()
