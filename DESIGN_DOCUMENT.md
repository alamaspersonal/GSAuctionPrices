# GSAuctionPrices — Design Document & PRD

**Product**: Sheep & Goat Auction Price Dashboard
**Version**: 1.0 — Design Phase
**Date**: March 2026
**Author**: Anthony Lamas

---

## 1. Executive Summary

### The Problem

USDA Livestock Mandatory Price Reports (LMPR) are the richest public source of sheep and goat auction data in the United States — covering ~10,000 lot entries every 100 days across 29 auction markets in 17 states. But this data is consumed through dense PDF-style reports, flat CSV exports, and technical jargon that only seasoned market reporters understand.

A goat producer trying to figure out if their 60 lb Boer kids are priced competitively has to wade through reports organized by slug ID, decode what "Selection 1-2, Per Cwt, F.O.B." means, and mentally convert $280/cwt to a per-head price. The information exists — it's just inaccessible.

### The Solution

A web dashboard that normalizes, searches, and visualizes USDA LMPR auction data through **intent-based filtering** — letting buyers, sellers, and analysts ask natural questions:

- _"What are 40–60 lb goat kids selling for in Texas?"_
- _"Which auction yard is paying the most for my hair breed ewes?"_
- _"How have slaughter lamb prices trended over the last 5 weeks?"_

### Data Foundation (Current Dataset: `GSAuctionPrices/lmpr_data/`)

| Metric                   | Value                                      |
| ------------------------ | ------------------------------------------ |
| Total lot entries        | 9,768                                      |
| CSV files (slug reports) | 31                                         |
| Auction markets          | 29                                         |
| States covered           | 17                                         |
| Date window              | Rolling 100 days                           |
| Species split            | 52% Sheep / 47% Goats                      |
| Commodity split          | 82% Slaughter / 6% Feeder / 8% Replacement |
| Pricing units            | 80% Per Cwt / 20% Per Head                 |
| Weight range             | 4–340 lbs (median 85 lbs)                  |
| Price range (Cwt)        | $20–$670/cwt (median $265)                 |
| Price per lb range       | $0.20–$6.70/lb                             |

---

## 2. User Personas

### Persona A — The Commercial Producer

> _"I have 200 head of slaughter-weight hair lambs and I need to know which sale barn will net me the best return this week."_

| Attribute        | Detail                                                                         |
| ---------------- | ------------------------------------------------------------------------------ |
| **Name**         | Marcos, Central TX Rancher                                                     |
| **Herd**         | 200+ Dorper/Katahdin hair sheep, rotational grazing                            |
| **Sale volume**  | 40–80 head every 6–8 weeks                                                     |
| **Key question** | "Where's the best price for 100–130 lb hair lambs right now?"                  |
| **Data needs**   | Regional price comparison, receipts volume (liquidity signal), trend direction |
| **Pain point**   | Has to call 3–4 sale barns to get price ideas; PDFs are too slow               |
| **Device**       | Phone at the barn, tablet at the kitchen table                                 |
| **Frequency**    | Checks prices 2–3x/week, especially Sun–Tue before Wednesday sales             |

**Primary workflows**: Seller Mode → compare prices across markets, Trend charts for timing

---

### Persona B — The Hobbyist / Breeder

> _"I raise registered Boer goats and I need to know what replacement-quality does are commanding — specifically hair breed, bred, young ewes or nannies."_

| Attribute        | Detail                                                                                                              |
| ---------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Name**         | Rachel, Small Acreage in KY                                                                                         |
| **Herd**         | 15–25 registered Boer does, sells kids and replacement stock                                                        |
| **Sale volume**  | 5–15 animals/year at auction + private treaty                                                                       |
| **Key question** | "What are bred replacement nannies going for? What about pygmy goats?"                                              |
| **Data needs**   | Replacement-specific filters, age breakdowns (Young 2-4 yrs vs Yearling), `lot_desc` tags like "Fancy" or "Pygmies" |
| **Pain point**   | Most dashboards lump all goats together; needs to filter to Replacement + Nannies/Does specifically                 |
| **Device**       | Phone predominantly                                                                                                 |
| **Frequency**    | Weekly browsing, spikes before she lists animals or attends a sale                                                  |

**Primary workflows**: Buyer Mode → filter Replacement, specific class + lot_desc, Detail View with age breakdown

---

### Persona C — The Market Trader / Speculator

> _"I buy feeder kids at 30–40 lbs, grow them out to 70–80 lbs, and sell as slaughter. I need the price spread between feeder and slaughter to calculate my margin."_

| Attribute        | Detail                                                                                                           |
| ---------------- | ---------------------------------------------------------------------------------------------------------------- |
| **Name**         | Demetrius, Feedlot Operator in MO                                                                                |
| **Operation**    | Buys 100–300 feeder goats/month, feeds for 60–90 days                                                            |
| **Key question** | "What's the buy price at 40 lbs and the sell price at 80 lbs? What's my break-even?"                             |
| **Data needs**   | Side-by-side feeder vs slaughter pricing, Profitability Calculator, weight-price scatter to understand the curve |
| **Pain point**   | No tool connects the buy-side (feeder) and sell-side (slaughter) prices in one view                              |
| **Device**       | Desktop for analysis, phone for spot-checking                                                                    |
| **Frequency**    | Daily during buying weeks, weekly for trend analysis                                                             |

**Primary workflows**: Profitability Calculator, Price vs Weight scatter plot, Trend overlay (feeder vs slaughter)

---

## 3. Detailed User Flows

### 3.1 The Search Journey — Buyer Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                        ENTRY POINT                                  │
│  Dashboard loads → "At-a-Glance" widgets visible                    │
│  Default: all species, all commodities, last 14 days                │
└───────────────────────┬──────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 1 — Pick Your Intent                                          │
│  Three large segmented buttons:                                     │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐    │
│  │ 🥩 Meat Market  │ │ 🌱 Feeder/Grow  │ │ 🐏 Breeding Stock  │    │
│  │   (Slaughter)   │ │   (Feeder)      │ │   (Replacement)    │    │
│  └─────────────────┘ └─────────────────┘ └─────────────────────┘    │
│  Selecting one pre-filters `commodity` and adjusts available        │
│  classes/grades contextually                                        │
└───────────────────────┬──────────────────────────────────────────────┘
                        │  User selects "Meat Market"
                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 2 — Pick Species                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                            │
│  │  🐑 Sheep │ │  🐐 Goats │ │   Both   │                          │
│  └──────────┘ └──────────┘ └──────────┘                            │
│  Selecting "Goats" narrows available classes to:                    │
│  Kids (1494) · Nannies/Does (950) · Bucks/Billies (727)            │
│  · Wethers (374) · Wether Kids (197)                               │
└───────────────────────┬──────────────────────────────────────────────┘
                        │  User selects "Goats"
                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 3 — Refine (Basic Filters visible by default)                 │
│                                                                      │
│  Class:     ○ All  ● Kids  ○ Nannies  ○ Bucks  ○ Wethers           │
│  Weight:    ═══════●────────●═══════  40 – 80 lbs                   │
│  State:     [ TX ✕ ] [ OK ✕ ] [+ Add State]                        │
│                                                                      │
│  ▸ Advanced Filters                                                  │
│     Grade:  ☑ Selection 1  ☑ Selection 1-2  ☐ Choice  ☐ Good       │
│     Lot:    ☐ Pygmies  ☐ Fancy  ☐ Yearlings                        │
│     Price:  ═══════●────────●═══════  $1.50 – $4.00/lb             │
│     Market: [ Search auction yards... ]                              │
└───────────────────────┬──────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 4 — Results (Card Grid)                                       │
│                                                                      │
│  "42 lots found"                Sort: [ Lowest $/lb ▾ ]             │
│                                                                      │
│  ┌─ Card ────────┐ ┌─ Card ────────┐ ┌─ Card ────────┐             │
│  │ 🟢 Slaughter  │ │ 🟢 Slaughter  │ │ 🟢 Slaughter  │             │
│  │ Kids          │ │ Kids          │ │ Wether Kids   │             │
│  │ $258/cwt      │ │ $272/cwt      │ │ $245/cwt      │             │
│  │ 65 lbs · 12hd │ │ 48 lbs · 6hd  │ │ 72 lbs · 3hd  │             │
│  │ San Angelo TX │ │ Salem, VA     │ │ Jackson, MO   │             │
│  └───────────────┘ └───────────────┘ └───────────────┘             │
│                                                                      │
│  ┌─ Card ────────┐ ┌─ Card ────────┐ ...                           │
└───────────────────────┬──────────────────────────────────────────────┘
                        │  User taps a card
                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 5 — Detail View (slide-up panel or modal)                     │
│                                                                      │
│  See Section 3.4 for full Detail View spec                          │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.2 The Search Journey — Seller Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│  SELLER MODE (tab toggle at top of dashboard)                       │
│                                                                      │
│  "Describe Your Animal"                                              │
│                                                                      │
│  Species: [ Goats ▾ ]    Class: [ Kids ▾ ]                          │
│  Weight:  ═══●═══  ~60 lbs                                          │
│  Grade:   [ Selection 1-2 ▾ ]  (optional)                           │
│                                                                      │
│  [ Find Best Markets → ]                                             │
└───────────────────────┬──────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│  MARKET COMPARISON TABLE                                             │
│                                                                      │
│  Time Range: ○ 2 wk  ● 30 d  ○ 90 d                                │
│                                                                      │
│  ┌──────────────────────┬────────┬─────────┬───────┬──────┬───────┐ │
│  │ Auction Yard         │ State  │ Avg $/lb│ Avg $ │ Vol  │ Trend │ │
│  │                      │        │         │  /Hd  │ (hd) │       │ │
│  ├──────────────────────┼────────┼─────────┼───────┼──────┼───────┤ │
│  │ San Angelo           │ TX     │ $3.12   │ $187  │ 84   │  ↑ 4% │ │
│  │ New Holland          │ PA     │ $2.98   │ $179  │ 142  │  ↓ 2% │ │
│  │ Kalona               │ IA     │ $2.85   │ $171  │ 63   │  → 0% │ │
│  │ Bowling Green        │ KY     │ $2.74   │ $164  │ 31   │  ↑ 7% │ │
│  └──────────────────────┴────────┴─────────┴───────┴──────┴───────┘ │
│                                                                      │
│  Click a row → expands to show 5-week trend line for that market    │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.3 Zero Results Handling

Zero results is a real risk — the dataset is specialized and sparse for some combinations. The app handles this progressively:

**Level 1 — Widen Weight** (most common cause)

> "No lots found for 40–50 lb Slaughter Kids in TX."
> → **Suggestion**: "Expand weight range to 30–60 lbs? (12 lots found)"
> → Button: `[ Show 30–60 lbs ]`

**Level 2 — Widen Geographic**

> "No lots found for Feeder Hair Lambs in CO."
> → **Suggestion**: "Try nearby states? MT (8 lots), SD (3 lots)"
> → Clickable state chips

**Level 3 — Widen Time**

> "No lots found for Replacement Nannies in the last 14 days."
> → **Suggestion**: "Expand to last 30 days? (7 lots found)"
> → Button: `[ Show Last 30 Days ]`

**Level 4 — Show Nearest**

> If all expansions still yield nothing:
> → "No exact matches. Here are the closest lots:" → Show the 5 nearest lots by weight distance, ranked by `|user_target_weight - avg_weight|`

**Implementation**: The API returns a `suggestions` object alongside `results`:

```json
{
  "results": [],
  "count": 0,
  "suggestions": {
    "weight_expanded": { "range": [30, 60], "count": 12 },
    "states_nearby": [
      { "state": "MT", "count": 8 },
      { "state": "SD", "count": 3 }
    ],
    "time_expanded": { "days": 30, "count": 7 },
    "nearest_lots": [ ... ]   // 5 closest by weight
  }
}
```

### 3.4 Detail View (Lot Deep-Dive)

When a user taps/clicks a card, a slide-up panel (mobile) or side panel (desktop) opens:

```
┌──────────────────────────────────────────────────────────────────────┐
│  ✕ Close                                                             │
│                                                                      │
│  ┌─ HEADER ──────────────────────────────────────────────────────┐  │
│  │  🟢 Slaughter · Goats · Kids                                  │  │
│  │  Selection 1-2  ·  Avg Dressing  ·  Medium Frame              │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─ PRICE BLOCK ─────────────────────────────────────────────────┐  │
│  │          $280.00 /cwt                                          │  │
│  │    ≈ $2.80/lb   ·   ≈ $168.00/hd                             │  │
│  │    Range: $265 – $295 /cwt                                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─ ANIMAL ──────────────────────────────────────────────────────┐  │
│  │  Weight: 60 lbs (range 55–65)                                 │  │
│  │  Bracket: 40–80 lbs                                           │  │
│  │  Head Count: 12                                               │  │
│  │  Lot Notes: —                                                 │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─ MARKET ──────────────────────────────────────────────────────┐  │
│  │  📍 Producers Livestock - San Angelo, TX                      │  │
│  │  📅 Feb 9, 2026  (Final Report)                               │  │
│  │  Receipts: 681 hd  (last wk: 592  ·  last yr: 710)           │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─ 5-WEEK TREND (for 40-80lb Slaughter Kids at this market) ───┐  │
│  │  $3.20 ┤                                                      │  │
│  │  $3.00 ┤          ●                                           │  │
│  │  $2.80 ┤     ●────●────●                                     │  │
│  │  $2.60 ┤  ●                ●                                  │  │
│  │        └──┬────┬────┬────┬────┬                               │  │
│  │         W1   W2   W3   W4   W5                                │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─ MARKET NARRATIVE ────────────────────────────────────────────┐  │
│  │  "Compared to last sale: Slaughter goat kids sold steady to   │  │
│  │   5.00 higher. Nannies sold 10.00–20.00 higher on a light    │  │
│  │   test. Supply included 60% goats and 40% sheep..."          │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─ ACTIONS ─────────────────────────────────────────────────────┐  │
│  │  [ 🧮 Profitability Calculator ]   [ 📊 Compare Markets ]     │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. Data Visualization & UI Components

### 4.1 The Dashboard — At-a-Glance Widgets

The top of the dashboard shows 4 summary widgets, refreshed with every filter change:

```
┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│  🐐 Goat Kids   │  │  🐑 Hair Lambs  │  │  📊 Volume       │  │  🔥 Top Gainer  │
│  Avg: $2.79/lb  │  │  Avg: $2.57/lb  │  │  9,768 lots      │  │  Feeder Kids    │
│  ↑ 3.2% (2 wk)  │  │  ↓ 1.4% (2 wk)  │  │  29 markets      │  │  ↑ 12% (2 wk)  │
│  (Slaughter)     │  │  (Slaughter)     │  │  17 states       │  │  San Angelo TX  │
└─────────────────┘  └─────────────────┘  └──────────────────┘  └─────────────────┘
```

| Widget                     | Data Source                                               | Calculation                                                          |
| -------------------------- | --------------------------------------------------------- | -------------------------------------------------------------------- |
| **Species Avg Price** (x2) | All slaughter lots for Goats/Sheep in last 14 days        | Weighted avg of `avg_price / 100` (cwt→lb), weighted by `head_count` |
| **Volume**                 | All detail rows in current filter window                  | Simple counts                                                        |
| **Top Gainer**             | Compare weekly avg for each species+commodity+class combo | Largest % increase vs 2 weeks ago                                    |

### 4.2 The Filter System — Basic vs Advanced

The filter panel is designed to **not overwhelm**. Filters are split into two tiers:

#### Basic Filters (always visible)

| Filter  | Type               | Options                                      |
| ------- | ------------------ | -------------------------------------------- |
| Intent  | Segmented control  | Meat Market · Feeder/Grow · Breeding Stock   |
| Species | Toggle             | Sheep · Goats · Both                         |
| Weight  | Dual-thumb slider  | 0–350 lbs (snaps to 10lb increments)         |
| State   | Multi-select chips | Top 6 states shown, "More" expands full list |

#### Advanced Filters (collapsed behind "▸ Advanced" toggle)

| Filter            | Type                | Options                                                                                          |
| ----------------- | ------------------- | ------------------------------------------------------------------------------------------------ |
| Class             | Multi-select chips  | Contextual — only shows classes valid for selected species + commodity                           |
| Quality Grade     | Multi-select chips  | Selection 1, 1-2, 1-3, 2, 3, Choice, Good, Utility, Cull                                         |
| Lot Descriptor    | Multi-select        | Pygmies, Yearlings, Fancy, Thin Fleshed, etc.                                                    |
| Price Range       | Dual-thumb slider   | $/lb or $/cwt depending on unit toggle                                                           |
| Auction Yard      | Searchable dropdown | All 29 markets                                                                                   |
| Date Range        | Presets + custom    | Last 7d · 14d · 30d · 90d · Custom                                                               |
| Dressing          | Chips               | Average · High · Low                                                                             |
| Age (Replacement) | Chips               | Only appears for Replacement intent — Kids<1yr · Yearling 1-2 · Young 2-4 · Middle 4-6 · Aged 6+ |

#### Contextual Class Mapping

When the user selects Species + Intent, the Class filter auto-populates with only relevant options:

| Species | Intent   | Available Classes                                                                                                        |
| ------- | -------- | ------------------------------------------------------------------------------------------------------------------------ |
| Goats   | Meat     | Kids (1494) · Nannies/Does (950) · Bucks/Billies (727) · Wethers (374) · Wether Kids (197)                               |
| Goats   | Feeder   | Kids (512) · Wether Kids (31)                                                                                            |
| Goats   | Breeding | Nannies/Does (270) · Bucks/Billies (11) · Families (58)                                                                  |
| Sheep   | Meat     | Hair Breeds (1636) · Wooled & Shorn (922) · Ewes (551) · Hair Ewes (482) · Hair Bucks (289) · Bucks (262) · Wooled (135) |
| Sheep   | Feeder   | Hair Lambs (203) · Lambs (159) · Hair Breeds (6)                                                                         |
| Sheep   | Breeding | Hair Ewes (273) · Families (87) · Ewes (79) · Hair Bucks (18)                                                            |

These counts are pre-computed from the database and shown as badges to give users a sense of data density before filtering.

### 4.3 Color System

#### Commodity Colors (primary visual signal)

| Commodity   | Color      | Hex       | CSS Variable          | Rationale                          |
| ----------- | ---------- | --------- | --------------------- | ---------------------------------- |
| Slaughter   | Sage Green | `#50C878` | `--color-slaughter`   | Market-ready, the "money" color    |
| Feeder      | Sky Blue   | `#4A90D9` | `--color-feeder`      | Growing, developing, calm          |
| Replacement | Warm Amber | `#F5A623` | `--color-replacement` | Investment, breeding stock premium |

#### Species Accent (subtle border/badge)

| Species | Color      | Hex       | CSS Variable    |
| ------- | ---------- | --------- | --------------- |
| Sheep   | Slate Blue | `#607D8B` | `--color-sheep` |
| Goats   | Terracotta | `#C67A5C` | `--color-goat`  |

#### Trend Signals

| Direction   | Color     | Icon |
| ----------- | --------- | ---- |
| Rising ≥2%  | `#4CAF50` | ↑    |
| Falling ≥2% | `#F44336` | ↓    |
| Stable <2%  | `#9E9E9E` | →    |

### 4.4 Trend Visualization

#### Chart A — Price vs. Weight Scatter Plot

- **X-axis**: Average weight (lbs)
- **Y-axis**: Price per lb ($)
- **Dot color**: Commodity (green/blue/amber)
- **Dot size**: Head count (larger dots = larger lots)
- **Interaction**: Hover to see lot details tooltip (market, date, grade)
- **Insight**: Visually reveals the price curve — lighter animals tend to have higher per-lb prices, heavier animals trend lower per lb. This is the critical insight for feeder operators.

#### Chart B — 5-Week Price Trend Line

- **X-axis**: Week (W1–W5+)
- **Y-axis**: Weighted avg price per lb
- **Line**: Solid colored line for the primary series
- **Band**: Faint shaded area showing min–max price range per week
- **Overlays**: Option to overlay feeder vs slaughter lines simultaneously (for margin analysis)
- **Interaction**: Click a week point to expand and see the individual lot entries that contributed to that week's average

---

## 5. Wireframe Specifications

### 5.1 Layout — Desktop (≥1024px)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  HEADER BAR                                                                     │
│  [🐑 GSAuction]    [ Buyer │ Seller ]    [ $/Cwt ⟷ $/Lb ⟷ $/Hd ]    [ ⚙ ]   │
├────────────────────┬─────────────────────────────────────────────────────────────┤
│  FILTER PANEL      │  MAIN CONTENT AREA                                         │
│  (280px fixed)     │                                                             │
│                    │  ┌─ At-a-Glance Widgets ──────────────────────────────────┐ │
│  Intent Buttons    │  │ Widget · Widget · Widget · Widget                      │ │
│  Species Toggle    │  └────────────────────────────────────────────────────────┘ │
│  Weight Slider     │                                                             │
│  State Chips       │  "142 lots found"              Sort: [ Lowest $/lb ▾ ]     │
│                    │                                                             │
│  ▸ Advanced        │  ┌─ Card ─┐ ┌─ Card ─┐ ┌─ Card ─┐ ┌─ Card ─┐            │
│    Grade Chips     │  │        │ │        │ │        │ │        │            │
│    Class Chips     │  └────────┘ └────────┘ └────────┘ └────────┘            │
│    Lot Desc        │  ┌─ Card ─┐ ┌─ Card ─┐ ┌─ Card ─┐ ┌─ Card ─┐            │
│    Price Slider    │  │        │ │        │ │        │ │        │            │
│    Market Select   │  └────────┘ └────────┘ └────────┘ └────────┘            │
│    Date Range      │                                                             │
│                    │  ┌─ Trend Charts ─────────────────────────────────────────┐ │
│  ┌──────────────┐  │  │ [ Scatter ] [ Trend Line ]                            │ │
│  │ 🧮 Profit    │  │  │                                                       │ │
│  │ Calculator   │  │  │  (chart renders here)                                 │ │
│  │ (collapsed)  │  │  │                                                       │ │
│  └──────────────┘  │  └───────────────────────────────────────────────────────┘ │
├────────────────────┴─────────────────────────────────────────────────────────────┤
│  DETAIL PANEL (slides in from right, 480px, when a card is clicked)             │
│  See Section 3.4                                                                 │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Layout — Mobile (<768px)

```
┌──────────────────────────┐
│  HEADER BAR              │
│  [🐑] [Buyer│Seller] [⚙] │
├──────────────────────────┤
│  At-a-Glance (2x2 grid)  │
│  ┌────────┐ ┌────────┐   │
│  │goat avg│ │sheep avg│  │
│  └────────┘ └────────┘   │
│  ┌────────┐ ┌────────┐   │
│  │ volume │ │top gain│   │
│  └────────┘ └────────┘   │
├──────────────────────────┤
│  FILTER BAR (horizontal  │
│  scroll, compact)        │
│                          │
│  [🥩 Meat ✕] [🐐 Goats]  │
│  [40-80 lbs] [TX] [▸ More│
├──────────────────────────┤
│  "42 lots"   [Sort ▾]    │
│                          │
│  ┌── Card (full-width) ──│
│  │  🟢 Kids · Sel 1-2    │
│  │  $2.80/lb · 60 lbs    │
│  │  San Angelo TX · Feb 9│
│  └────────────────────────│
│  ┌── Card ────────────────│
│  │  ...                   │
│  └────────────────────────│
├──────────────────────────┤
│  [ 📊 Trends ] FAB       │
│  (floating action button) │
└──────────────────────────┘

Tap card → full-screen slide-up
Tap "▸ More" → filter drawer slides up
Tap "📊 Trends" → chart view slides up
```

### 5.3 Design System

#### Typography

| Role                 | Font           | Size    | Weight  | Rationale                                                         |
| -------------------- | -------------- | ------- | ------- | ----------------------------------------------------------------- |
| **Body / UI**        | Inter          | 14–16px | 400–500 | Highly legible at small sizes, excellent on low-res screens       |
| **Headings**         | Inter          | 20–28px | 700     | Consistent family, no extra font load                             |
| **Numbers / Prices** | JetBrains Mono | 18–32px | 700     | Monospaced for price alignment; tabular nums for scanning columns |
| **Narrative text**   | Inter          | 13px    | 400     | Slightly smaller for market commentary blocks                     |

> **Field legibility note**: Inter was chosen because it has tall x-height, open counters, and was designed for computer screens. Critical for farmers reading on a phone in direct sunlight — we pair this with high-contrast dark mode as the default.

#### Color Palette

```
// Core dark theme (default — better for outdoor/sunlight contrast)
--bg-primary:     #0F1117    // Near-black, blue-tinted
--bg-card:        #1A1D27    // Card surface
--bg-elevated:    #242836    // Elevated panels, modals
--border:         #2E3345    // Subtle borders
--text-primary:   #F0F0F5    // Primary text (high contrast)
--text-secondary: #9CA3AF    // Secondary / muted text
--text-tertiary:  #636B7E    // Tertiary / labels

// Commodity signals
--color-slaughter: #50C878
--color-feeder:    #4A90D9
--color-replace:   #F5A623

// Species accents
--color-sheep:     #607D8B
--color-goat:      #C67A5C

// Trend signals
--color-up:        #4CAF50
--color-down:      #F44336
--color-flat:      #9E9E9E

// Interactive
--color-accent:    #6366F1   // Primary action buttons
--color-hover:     #818CF8   // Hover state
```

#### Button States

| State           | Background       | Border           | Text              | Shadow                          |
| --------------- | ---------------- | ---------------- | ----------------- | ------------------------------- |
| Default         | `--bg-elevated`  | `--border`       | `--text-primary`  | none                            |
| Hover           | `--color-hover`  | `--color-accent` | white             | `0 0 12px rgba(99,102,241,0.3)` |
| Active/Selected | `--color-accent` | `--color-accent` | white             | inner glow                      |
| Disabled        | `--bg-card`      | `--border`       | `--text-tertiary` | none                            |

#### Card Component

| State    | Effect                                                        |
| -------- | ------------------------------------------------------------- |
| Default  | `--bg-card` background, `--border` 1px border, 8px radius     |
| Hover    | Translate Y -2px, subtle shadow bloom, border lightens        |
| Selected | Left border thickens to 3px commodity color, background tints |
| Loading  | Skeleton pulse animation (3 placeholder lines)                |

---

## 6. Technical Design & Edge Cases

### 6.1 Sync Logic — Data Freshness

#### How USDA Reports Work

- Auction reports are published **the day of the sale** (usually afternoons/evenings)
- Most auctions run **1x per week** on set days (e.g., every Wednesday)
- Summary reports (weekly state rollups) publish **weekly** (typically Fridays)
- The MARS API provides data with `published_date` timestamps

#### Sync Strategy

| Event              | Frequency                                     | Action                                                    |
| ------------------ | --------------------------------------------- | --------------------------------------------------------- |
| **Cron fetch**     | Every 6 hours (6:00, 12:00, 18:00, 00:00 UTC) | Run `get_lmpr_data.py` → `normalizer.py` → upsert into DB |
| **Startup sync**   | On backend boot                               | If last sync was >6 hours ago, trigger a full sync        |
| **Manual refresh** | Admin endpoint `POST /api/admin/sync`         | Force-trigger a sync cycle                                |
| **Data window**    | Rolling 100 days                              | Drop entries older than 100 days from the active dataset  |

#### Freshness Indicator in the UI

```
"Data as of Feb 9, 2026 6:00 PM  ·  Next sync in 2h"
```

The header bar shows when data was last refreshed, sourced from the most recent `published_date` in the DB.

### 6.2 Calculators — Precise Math

#### Unit Converter: Price per Cwt ↔ Price per Lb ↔ Price per Head

The API always returns all three pre-computed values. Client-side toggles just switch which is displayed.

```
Given from API:
  price_unit     = "Per Cwt"   or   "Per Unit"
  avg_price      = the reported number
  avg_weight     = lbs

If price_unit == "Per Cwt":
  price_per_lb   = avg_price / 100
  price_per_head = (avg_price / 100) * avg_weight

If price_unit == "Per Unit" (Per Head):
  price_per_head = avg_price
  price_per_lb   = avg_price / avg_weight           // requires avg_weight > 0
  price_per_cwt  = (avg_price / avg_weight) * 100   // derived cwt equivalent
```

**Edge case**: If `avg_weight == 0` or `null`, we cannot derive per-lb from per-head. In that case, display the original unit only and show a ⚠️ tooltip: "Weight not reported — conversion unavailable."

#### Live Weight to Carcass Weight Converter

This is useful for buyers evaluating meat yield. USDA `dressing` field tells us the yield category:

| Dressing Grade | Typical Yield % | Dataset Rows |
| -------------- | --------------- | ------------ |
| High           | 54%             | 271 (3%)     |
| Average        | 50%             | 7,667 (94%)  |
| Low            | 46%             | 89 (1%)      |

```
carcass_weight = live_weight * dressing_pct

// Example: 80 lb goat kid, Average dressing
carcass_weight = 80 * 0.50 = 40 lbs

price_per_lb_carcass = price_per_head / carcass_weight
// If bought at $200/head:
price_per_lb_carcass = $200 / 40 = $5.00/lb hanging weight
```

The UI shows this as a toggle within the Detail View:

```
  Live:    80 lbs @ $2.50/lb = $200/hd
  Carcass: 40 lbs @ $5.00/lb (50% yield, Avg dressing)
```

#### Profitability Calculator

Inputs (user-adjustable sliders):

| Input                    | Default                       | Range       | Step  |
| ------------------------ | ----------------------------- | ----------- | ----- |
| Purchase Price           | Auto-filled from selected lot | —           | —     |
| Purchase Weight          | Auto-filled from selected lot | —           | —     |
| Target Sell Weight       | 120 lbs                       | 40–300 lbs  | 5 lbs |
| Feed Cost per lb of gain | $0.45/lb                      | $0.10–$1.50 | $0.05 |
| Mortality/Shrink %       | 3%                            | 0–15%       | 1%    |

Calculations:

```
weight_gain         = target_sell_weight - purchase_weight
feed_cost_total     = weight_gain * feed_cost_per_lb_gain
shrink_loss         = purchase_price * (mortality_pct / 100)
total_investment    = purchase_price + feed_cost_total + shrink_loss

break_even_per_lb   = total_investment / target_sell_weight
break_even_per_cwt  = break_even_per_lb * 100
break_even_per_head = total_investment

// Pull current market price for target weight class
current_market_avg  = (API query for same species/class at target_sell_weight)

margin_per_head     = (current_market_avg_per_lb * target_sell_weight) - total_investment
margin_pct          = margin_per_head / total_investment * 100
```

Example:

```
Buy 60 lb goat kid at $187/hd ($3.12/lb)
Target: sell at 80 lbs
Feed cost: $0.45/lb gain → 20 lbs * $0.45 = $9.00
Shrink: 3% → $5.61
Total investment: $187 + $9 + $5.61 = $201.61

Break-even at 80 lbs: $201.61 / 80 = $2.52/lb ($252/cwt)
Current market for 80 lb slaughter kids: $2.80/lb

Margin: ($2.80 * 80) - $201.61 = $224 - $201.61 = $22.39/hd (11.1%)  ✅
```

### 6.3 Offline Mode — Low-Signal Resilience

Farmers in rural areas (MT, SD, AR) will often have intermittent or no cellular signal. The app must degrade gracefully.

#### Strategy: Service Worker + IndexedDB Cache

| Component                    | Offline Behavior                                                        |
| ---------------------------- | ----------------------------------------------------------------------- |
| **App shell**                | Fully cached via Service Worker — instant load offline                  |
| **Last synced data**         | Stored in IndexedDB — all normalized entries from last successful fetch |
| **Filters**                  | Fully functional against cached data                                    |
| **Charts**                   | Render from cached data (Recharts works client-side)                    |
| **Profitability Calculator** | Fully functional (pure math, no API needed)                             |
| **Data sync**                | Queued — when connectivity resumes, background sync pulls latest        |

#### Offline Indicator

```
  🟢 Live Data (synced 2h ago)        // online
  🟡 Cached Data (synced 18h ago)     // offline, recent cache
  🔴 Offline — Showing Feb 2 data     // offline, stale cache
```

#### Cache Strategy

- **On first load**: Download all normalized entries for the rolling 100-day window (~10K rows, roughly 3–5 MB as JSON). Store in IndexedDB.
- **On subsequent visits**: If online, check `Last-Modified` header → incremental sync (only new entries since last sync). If offline, serve from IndexedDB.
- **Cache TTL**: 7 days. After 7 days without sync, show a warning but still allow browsing cached data.

### 6.4 Additional Edge Cases

| Edge Case                                   | Handling                                                                                                                                                                                                                |
| ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Duplicate reports** (Preliminary → Final) | The `final_ind` column is always "Final" in our dataset, but if a slug publishes both, keep only `final_ind == "Final"`                                                                                                 |
| **Column aliases across slugs**             | Normalizer has an explicit alias map (e.g., slugs 2922 and 3454 use `wtd_Avg_Price` instead of `avg_price`). Fail loudly if a new alias appears.                                                                        |
| **Outlier prices**                          | Prices below $0.10/lb or above $8.00/lb flagged as potential data errors. Show with a ⚠️ badge but don't exclude.                                                                                                       |
| **Zero head count**                         | Rare but possible. Show the entry but don't include in weighted averages.                                                                                                                                               |
| **Missing weight**                          | ~32 rows have no `avg_weight`. Cannot compute per-lb price. Show only the original unit.                                                                                                                                |
| **"Hogs" and "Sheep" (1 row) in class**     | The dataset has 6 "Hogs" entries and 1 "Sheep" class entry. Filter these out during normalization — they're data anomalies in sheep/goat reports.                                                                       |
| **Summary vs Auction**                      | 87% of records are individual auction reports, 13% are weekly state summaries. The summary records (slugs 2907, 2922, 3454) have different column naming. Tag with `is_summary: true` and let users toggle them on/off. |

---

## 7. Tech Stack & Architecture

| Layer             | Technology                                   | Notes                                                             |
| ----------------- | -------------------------------------------- | ----------------------------------------------------------------- |
| **Data Pipeline** | `get_lmpr_data.py` (existing)                | Fetches from USDA MARS API → raw CSVs                             |
| **Normalizer**    | `backend/normalizer.py` (new)                | CSV → unified schema → SQLite                                     |
| **Backend API**   | Python / FastAPI                             | REST API with filter, analytics, tool endpoints                   |
| **Database**      | SQLite (dev) → PostgreSQL (prod)             | Single `auction_entries` table + materialized views for analytics |
| **Frontend**      | React + Vite                                 | SPA dashboard                                                     |
| **Charts**        | Recharts                                     | Scatter, line, bar — interactive tooltips                         |
| **Offline**       | Service Worker + IndexedDB                   | Full offline capability                                           |
| **Hosting**       | Vercel (frontend) + Railway/Render (backend) | Or self-hosted                                                    |

---

## Appendix A — Complete Class Taxonomy

### Goats (4,624 lots)

| Class         | Slaughter | Feeder | Replacement | Total |
| ------------- | --------- | ------ | ----------- | ----- |
| Kids          | 1,494     | 512    | —           | 2,006 |
| Nannies/Does  | 950       | —      | 270         | 1,220 |
| Bucks/Billies | 727       | —      | 11          | 738   |
| Wethers       | 374       | —      | —           | 374   |
| Wether Kids   | 197       | 31     | —           | 228   |
| Families      | —         | —      | 58          | 58    |

### Sheep (5,112 lots)

| Class          | Slaughter | Feeder | Replacement | Total |
| -------------- | --------- | ------ | ----------- | ----- |
| Hair Breeds    | 1,636     | 6      | —           | 1,642 |
| Wooled & Shorn | 922       | —      | —           | 922   |
| Hair Ewes      | 482       | —      | 273         | 755   |
| Ewes           | 551       | —      | 79          | 630   |
| Hair Bucks     | 289       | —      | 18          | 307   |
| Bucks          | 262       | —      | 1           | 263   |
| Hair Lambs     | —         | 203    | —           | 203   |
| Lambs          | —         | 159    | —           | 159   |
| Wooled         | 135       | —      | —           | 135   |
| Families       | —         | —      | 87          | 87    |
| Shorn          | 8         | —      | —           | 8     |

### Quality Grade Distribution (8,358 graded lots)

| Grade            | Count | %   |
| ---------------- | ----- | --- |
| Selection 1      | 1,791 | 21% |
| Selection 2      | 1,494 | 18% |
| Choice and Prime | 1,373 | 16% |
| Choice           | 1,100 | 13% |
| Selection 1-2    | 857   | 10% |
| Good             | 644   | 8%  |
| Selection 3      | 384   | 5%  |
| Good and Choice  | 283   | 3%  |
| Utility          | 142   | 2%  |
| Utility and Good | 141   | 2%  |
| Selection 2-3    | 98    | 1%  |
| Cull             | 30    | <1% |
| Cull and Utility | 21    | <1% |

---

## Appendix B — API Endpoint Reference

```
GET  /api/entries              # Filtered lot listing (paginated)
GET  /api/entries/:id          # Single lot detail + 5-week trend data
GET  /api/analytics/summary    # At-a-Glance widget data
GET  /api/analytics/compare    # Seller mode: market comparison table
GET  /api/analytics/trends     # Trend line data (weekly aggregates)
GET  /api/analytics/scatter    # Price vs Weight scatter data
POST /api/tools/convert        # Unit conversion (batch)
POST /api/tools/profitability  # Profitability calculator
POST /api/admin/sync           # Force data refresh
GET  /api/meta/classes         # Available classes for species+commodity
GET  /api/meta/markets         # All auction markets with counts
GET  /api/meta/freshness       # Last sync time, next sync, data window
```
