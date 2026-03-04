# GSAuctionPrices — Livestock Marketplace Dashboard

> Transform raw USDA LMPR livestock auction data (Sheep & Goats) into a searchable, filterable marketplace dashboard — built inside the existing `GSAuctionPrices` project.

## Existing Foundation

The project already has:
- **[get_lmpr_data.py](file:///Users/anthonylamas/Programming/GSAuctionPrices/get_lmpr_data.py)** — Fetches past 100 days of LMPR data from 31 slug IDs via the USDA MARS API → outputs per-slug CSVs
- **[visualize_lmpr.py](file:///Users/anthonylamas/Programming/GSAuctionPrices/visualize_lmpr.py)** — Generates matplotlib chart PNGs (category breakdown, geographic distribution, price distribution)
- **[all_columns.csv](file:///Users/anthonylamas/Programming/GSAuctionPrices/all_columns.csv)** — Documents all 79 columns with aliasing issues (e.g., `avg_price` vs `wtd_Avg_Price`, `weight_break_low` vs `weight_Break_Low`)
- **9,789 rows** across 29 auction markets in 17 states

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Backend** | Python / FastAPI | Matches existing Python pipeline; you already use FastAPI in DAWLab |
| **Database** | SQLite (dev) → PostgreSQL (prod) | Lightweight for dev; your SpecialtyCropDashboard uses SQLite similarly |
| **Data Pipeline** | Existing [get_lmpr_data.py](file:///Users/anthonylamas/Programming/GSAuctionPrices/get_lmpr_data.py) + new normalizer module | Reuse the MARS API fetcher, add a normalization step |
| **Frontend** | React + Vite | Fast dev server, modern tooling |
| **Charts** | Recharts (React) | Lightweight, composable, good for scatter/line/bar |
| **Styling** | Vanilla CSS with CSS custom properties | Per project guidelines — dark theme consistent with your existing chart palette |

### Project Structure (new files within `GSAuctionPrices/`)

```
GSAuctionPrices/
├── get_lmpr_data.py          # existing — MARS API fetcher
├── visualize_lmpr.py         # existing — matplotlib charts
├── all_columns.csv           # existing — column inventory
├── lmpr_data/                # existing — raw CSVs
│
├── backend/                  # [NEW] FastAPI backend
│   ├── main.py               # FastAPI app, CORS, lifespan
│   ├── normalizer.py         # CSV → normalized AuctionEntry records
│   ├── database.py           # SQLite setup, init from normalized data
│   ├── models.py             # Pydantic models (AuctionEntry schema)
│   ├── routers/
│   │   ├── entries.py        # GET /entries with intent-based filters
│   │   ├── analytics.py      # GET /analytics (trends, comparisons)
│   │   └── tools.py          # POST /tools/convert, /tools/profitability
│   └── requirements.txt
│
└── frontend/                 # [NEW] React + Vite dashboard
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── src/
    │   ├── main.jsx
    │   ├── App.jsx
    │   ├── index.css          # Design system (dark theme, variables)
    │   ├── components/
    │   │   ├── FilterPanel.jsx       # Intent-based + technical filters
    │   │   ├── AuctionCard.jsx       # Single auction entry card
    │   │   ├── CardGrid.jsx          # Responsive card grid
    │   │   ├── TrendChart.jsx        # Price trend line / scatter plot
    │   │   ├── MarketCompare.jsx     # Seller's price comparison table
    │   │   ├── UnitConverter.jsx     # Cwt ↔ Per Head toggle
    │   │   └── ProfitCalculator.jsx  # Break-even slider tool
    │   └── hooks/
    │       └── useAuctionData.js     # Data fetching + filter state
    └── public/
```

---

## Pillar 1 — Data Normalization & Strategy

### The Problem

Raw MARS API data has **column aliasing** across different slug reports:
- `avg_price` vs `wtd_Avg_Price`
- `weight_break_low` vs `weight_Break_Low`
- `avg_weight` vs `wtd_avg_wt`
- `published_date` vs `published_Date`

Some columns only appear in 2–3 of the 31 files (e.g., `region_name`, `delivery_month`, `geographical_indicator`).

### Normalization Pipeline

```
[Raw CSVs in lmpr_data/] 
    → normalizer.py (alias resolution, type coercion, derived fields) 
    → SQLite DB (uniform AuctionEntry rows)
    → FastAPI serves normalized data
```

#### `normalizer.py` will:
1. **Merge column aliases** — map `wtd_Avg_Price` → `avg_price`, `weight_Break_Low` → `weight_break_low`, etc.
2. **Coerce types** — `avg_price` to float, `head_count` to int, `report_date` to ISO date
3. **Derive computed fields**:
   - `price_per_lb` — calculated from `avg_price / 100` when `price_unit == "Per Cwt"`, or `avg_price / avg_weight` when `price_unit == "Per Unit"`
   - `price_per_head` — inverse of above
   - `breed_type` — derived from `class` field: `"Hair"` if class contains "Hair Breeds", else `"Wooled"`
   - `buyer_intent` — mapped from `commodity`: Slaughter → `"meat"`, Feeder → `"feeder"`, Replacement → `"breeding"`
4. **Filter out non-detail rows** — skip rows where `_section == "Report Header"` (metadata-only rows)

### Normalized JSON Schema — `AuctionEntry`

```json
{
  "id": "1772-2026-02-09-001",
  "report_date": "2026-02-09",
  "published_date": "2026-02-09T18:47:05",

  "market": {
    "name": "Public Auction Yards",
    "city": "Billings",
    "state": "MT",
    "slug_id": 1772,
    "report_title": "Public Auction Yards Sheep & Goat Auction - Billings, MT",
    "market_type": "Auction"
  },

  "animal": {
    "species": "Sheep",
    "commodity": "Slaughter Sheep/Lambs",
    "class": "Wooled & Shorn",
    "breed_type": "Wooled",
    "quality_grade": "Selection 1-2",
    "lot_desc": null,
    "dressing": "Average",
    "age": null,
    "frame": "Medium",
    "muscle_grade": "1-2",
    "yield_grade": "1-2"
  },

  "pricing": {
    "price_unit": "Per Cwt",
    "avg_price": 264.58,
    "price_min": 255.00,
    "price_max": 275.00,
    "price_per_lb": 2.6458,
    "price_per_head": 312.20
  },

  "weight": {
    "avg_weight": 118,
    "weight_min": 113,
    "weight_max": 123,
    "weight_break_low": 100,
    "weight_break_high": 150
  },

  "volume": {
    "head_count": 4,
    "receipts": 343,
    "receipts_week_ago": 1301,
    "receipts_year_ago": 385
  },

  "derived": {
    "buyer_intent": "meat",
    "breed_type": "Wooled"
  },

  "narrative": "Compared to last sale: (1/19/26) Feeder lambs were all too lightly tested..."
}
```

---

## Pillar 2 — Buyer & Seller Filter Logic

### Intent-Based Filters (not just checkboxes)

#### Buyer Mode — "I want to buy..."

| Filter | Maps To | UI Element |
|--------|---------|------------|
| **Purpose** | `commodity` field | Segmented button: 🥩 Meat/Ethnic Market · 🌱 Feeder/Growing · 🐏 Breeding/Replacement |
| **Species** | `category` | Toggle: Sheep · Goats · Both |
| **Weight Range** | `avg_weight` | Dual-thumb slider (20–300 lbs) |
| **Breed Type** | derived `breed_type` | Chip toggle: Hair · Wooled · All |
| **Quality Grade** | `quality_grade_name` | Multi-select chips: Choice, Sel 1, Sel 1-2, Sel 1-3, Good, Utility, Cull |
| **Max Price** | `price_per_lb` | Slider with $/lb label |
| **Region** | `market_location_state` | State multi-select or map picker |

**Buyer Workflow**: A goat buyer for the ethnic meat market selects → Purpose: "Meat" → Species: "Goats" → Class auto-filtered to "Kids" and "Wethers" → Adjusts weight slider to 40–80 lbs → Sees cards sorted by lowest price per lb.

#### Seller Mode — "Where should I sell?"

| Filter | Maps To | UI Element |
|--------|---------|------------|
| **My Animal** | `category`, `class`, `avg_weight` | Preset form: "I have [Goat Kids] at [~60 lbs]" |
| **Compare By** | Aggregation level | Dropdown: By Market · By State · By Region |
| **Time Range** | `report_date` | Preset buttons: Last 2 weeks · Last month · Last 3 months |

**Seller Workflow**: A producer with 60-lb goat kids fills in the form → Dashboard shows a **comparison table** of avg price-per-lb at each auction yard that's reported similar animals → Sorted by highest avg price → Shows trend arrows (↑/↓) vs previous period.

#### Technical Filters (always available)

- **Date Range**: Calendar picker or quick presets
- **Auction Yard**: Searchable dropdown of `market_location_name` values
- **Price Unit Toggle**: Show all prices as "Per Cwt" or "Per Head" (instant conversion)

### API Design

```
GET /api/entries
  ?species=Goats
  &intent=meat                    # maps to commodity=Slaughter
  &weight_min=40&weight_max=80
  &breed_type=Hair
  &grade=Selection 1,Selection 1-2
  &state=TX,OK,MO
  &date_from=2026-01-01
  &sort_by=price_per_lb
  &sort_dir=asc
  &page=1&limit=50

GET /api/analytics/compare
  ?species=Goats
  &class=Kids
  &weight_min=40&weight_max=80
  &group_by=market                # returns per-market avg prices
  &period=30                      # days

GET /api/analytics/trends
  ?species=Sheep
  &commodity=Slaughter Sheep/Lambs
  &class=Wooled & Shorn
  &weight_bracket=100-150
  &period=90
```

---

## Pillar 3 — UI/UX Design

### Color System

| Commodity | Color | Hex | Rationale |
|-----------|-------|-----|-----------|
| Slaughter | Green | `#50C878` | "Market-ready" — the money color |
| Feeder | Blue | `#4A90D9` | "Growing" — calm, developing |
| Replacement | Amber | `#F5A623` | "Investment" — warm, premium |

Species accent: **Sheep** = slate blue border, **Goats** = warm terracotta border.

### Card-Based UI — `AuctionCard`

```
┌──────────────────────────────────────────────────┐
│ 🟢 SLAUGHTER                        Billings, MT │  ← commodity color dot + market location
│                                                   │
│  Wooled & Shorn Lambs           Selection 1-2     │  ← class (bold) + grade badge
│                                                   │
│   $264.58 /cwt      118 lbs      4 hd             │  ← BIG avg price, weight, head count
│   $255–275 range     113–123 lbs                   │  ← secondary: range details
│                                                   │
│   ≈ $2.65/lb  ·  ≈ $312/hd                        │  ← derived conversions (muted)
│                                                   │
│  Public Auction Yards    Feb 9, 2026               │  ← market name, date (footer)
│  📊 343 receipts (↓74% vs last wk)                 │  ← volume context
└──────────────────────────────────────────────────┘
```

**Visual Hierarchy** (boldest → lightest):
1. **Average Price** — largest font, white on dark
2. **Average Weight** + **Head Count** — secondary prominance
3. **Class + Grade** — distinctive, readable
4. **Commodity color dot** — instant scanability
5. **Market location + date** — footer, muted
6. **Derived prices** — small, utility text

### Trend Visualization

Two main charts, accessible from a "📊 Trends" tab:

1. **Price vs. Weight Scatter Plot** — Each dot = one auction entry, X = avg weight, Y = price per lb, colored by commodity. Lets buyers see the price curve (heavier animals tend to have lower per-lb prices).

2. **5-Week Price Trend Line** — Line chart showing weekly avg price for a selected species+class+weight bracket. Shows directional momentum. Include a faint band for min/max range per week.

Both charts built with **Recharts** — interactive tooltips showing the specific auction entry on hover.

---

## Pillar 4 — Added Value Features

### Unit Converter

A persistent toggle in the header or filter panel:

```
[ $/Cwt ]  ⟷  [ $/Head ]  ⟷  [ $/Lb ]
```

- When toggled, **every price on every card** recalculates instantly (client-side)
- Formula: `price_per_head = (avg_price_cwt / 100) × avg_weight`
- Formula: `price_per_lb = avg_price_cwt / 100`
- API always returns all three pre-computed in the `pricing` object

### Profitability Calculator

A slide-out panel or modal:

```
┌─ 🧮 Break-Even Calculator ─────────────────────┐
│                                                  │
│  Purchase Price:  $312.20 /hd  (auto-filled)     │
│  Purchase Weight: 60 lbs      (auto-filled)      │
│                                                  │
│  Target Sell Weight:  ═══●═══  120 lbs           │  ← slider
│  Feed Cost / lb gain: ═══●═══  $0.45             │  ← slider
│  Days on Feed (est):  ═══●═══  90 days           │  ← slider
│                                                  │
│  ─────────────────────────────────────────────   │
│  Feed Cost Total:           $27.00               │
│  Total Investment:          $339.20              │
│  Break-Even Price at 120lb: $2.83/lb             │
│  Break-Even Price (cwt):    $282.67/cwt          │
│                                                  │
│  Current Market for 120lb:  $245.00/cwt  ⚠️      │  ← pulled from real data
│  Margin:                    -$37.67/cwt  📉      │
└──────────────────────────────────────────────────┘
```

- Auto-fills purchase price/weight from whichever card the user clicked
- "Current Market" line queries the `/api/analytics/compare` endpoint for the target weight bracket
- Color-codes the margin: green = profitable, red = loss

---

## Mock Data Example

Here's a realistic normalized entry based on actual data from [lmpr_1772.csv](file:///Users/anthonylamas/Programming/GSAuctionPrices/lmpr_data/lmpr_1772.csv):

```json
{
  "id": "1772-20260209-0042",
  "report_date": "2026-02-09",
  "published_date": "2026-02-09T18:47:05",
  "market": {
    "name": "Public Auction Yards",
    "city": "Billings",
    "state": "MT",
    "slug_id": 1772,
    "report_title": "Public Auction Yards Sheep & Goat Auction - Billings, MT",
    "market_type": "Auction"
  },
  "animal": {
    "species": "Sheep",
    "commodity": "Slaughter Sheep/Lambs",
    "class": "Wooled & Shorn",
    "breed_type": "Wooled",
    "quality_grade": "Selection 1-2",
    "lot_desc": null,
    "dressing": "Average",
    "age": null,
    "frame": "Medium",
    "muscle_grade": "1-2",
    "yield_grade": "1-2"
  },
  "pricing": {
    "price_unit": "Per Cwt",
    "avg_price": 264.58,
    "price_min": 255.00,
    "price_max": 275.00,
    "price_per_lb": 2.65,
    "price_per_head": 312.20
  },
  "weight": {
    "avg_weight": 118,
    "weight_min": 113,
    "weight_max": 123,
    "weight_break_low": 100,
    "weight_break_high": 150
  },
  "volume": {
    "head_count": 4,
    "receipts": 343,
    "receipts_week_ago": 1301,
    "receipts_year_ago": 385
  },
  "derived": {
    "buyer_intent": "meat"
  },
  "narrative": "Compared to last sale: (1/19/26) Feeder lambs were all too lightly tested to develop a full market trend..."
}
```

---

## Primary User Workflows

### Workflow 1: Buyer — "Find goat kids for the ethnic meat market"
1. Open dashboard → defaults to **Buyer Mode**
2. Tap **🥩 Meat/Ethnic Market** purpose filter
3. Toggle species to **Goats**
4. Slide weight range to **40–80 lbs**
5. Cards populate with matching entries, sorted by lowest price per lb
6. Toggle unit display to **$/Head** to see total cost per animal
7. Click a card → detail panel shows narrative, volume context, and "Calculate Profitability" button

### Workflow 2: Seller — "Where's the best price for my 60-lb goat kids?"
1. Switch to **Seller Mode** tab
2. Fill in: Species = Goats, Class = Kids, Weight ≈ 60 lbs
3. Dashboard shows a **comparison table**: each auction yard that reported 40–80 lb goat kids in the last 30 days
4. Table columns: Market Name, State, Avg $/lb, Avg $/Head, Volume, Trend (↑↓)
5. Sorted by highest avg $/lb
6. Click a row → expands to show the 5-week trend line for that market

### Workflow 3: Analyst — "How are feeder lamb prices trending?"
1. Open **📊 Trends** tab
2. Select Species = Sheep, Commodity = Feeder, Weight Bracket = 60–90 lbs
3. View the **Price vs Weight scatter plot** — see how price varies by weight
4. View the **5-week trend line** — see directional price movement
5. Hover on any data point to see the specific auction entry details

---

## Verification Plan

### Automated Tests

**Backend unit tests** (pytest):
```bash
cd GSAuctionPrices/backend
python -m pytest tests/ -v
```

Tests to write:
- `test_normalizer.py` — Verify column alias resolution works correctly across CSVs with different column naming (e.g., slug 2922 uses `wtd_Avg_Price`, main slugs use `avg_price`). Verify derived field calculations (`price_per_lb`, `price_per_head`, `buyer_intent` mapping).
- `test_entries_api.py` — Verify filter parameters correctly narrow results (species, intent, weight range, state). Verify pagination and sorting.
- `test_tools_api.py` — Verify unit conversion math and profitability calculator formulas.

**Frontend** (dev server smoke test):
```bash
cd GSAuctionPrices/frontend
npm run dev
```
- Verify the dev server starts on port 5173 without errors

### Browser Verification
- Load the dashboard in the browser
- Apply buyer filters and verify cards reduce correctly
- Toggle unit converter and verify all card prices recalculate
- Open profitability calculator and verify math with hand-calculated values
- Check responsive layout at mobile/tablet/desktop breakpoints

### Manual Verification
- **Data integrity**: Compare a few normalized entries against the raw CSV rows to verify no data is lost or mismatched
- **Chart accuracy**: Spot-check a trend chart data point against the underlying filtered data
