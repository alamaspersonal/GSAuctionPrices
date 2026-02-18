"""
LMPR Data Visualization & Analysis

Generates charts showing the breakdown of livestock auction data
across all fetched LMPR reports. Saves charts as PNGs.

Usage:
    python visualize_lmpr.py
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os
import glob

# --------------------------------------------------
# Load all CSVs
# --------------------------------------------------

DATA_DIR = "lmpr_data"
OUTPUT_DIR = "charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

files = sorted(glob.glob(os.path.join(DATA_DIR, "lmpr_*.csv")))
if not files:
    print("No CSV files found in lmpr_data/. Run get_lmpr_data.py first.")
    exit(1)

dfs = []
for f in files:
    df = pd.read_csv(f, low_memory=False)
    dfs.append(df)

all_df = pd.concat(dfs, ignore_index=True)
print(f"Loaded {len(all_df):,} rows from {len(files)} files\n")

# --------------------------------------------------
# Color Palette
# --------------------------------------------------

COLORS = {
    'primary': '#4A90D9',
    'secondary': '#D94A4A',
    'accent': '#50C878',
    'warm': '#F5A623',
    'purple': '#9B59B6',
    'teal': '#1ABC9C',
    'palette': ['#4A90D9', '#D94A4A', '#50C878', '#F5A623', '#9B59B6',
                '#1ABC9C', '#E67E22', '#2ECC71', '#3498DB', '#E74C3C',
                '#9B59B6', '#F39C12', '#1ABC9C', '#E84393', '#00B894',
                '#FDCB6E', '#6C5CE7', '#A29BFE']
}

DARK_BG = '#1a1a2e'
CARD_BG = '#16213e'
TEXT_COLOR = '#e0e0e0'
GRID_COLOR = '#2a2a4a'


def style_ax(ax, title, xlabel='', ylabel=''):
    """Apply consistent dark styling to axes."""
    ax.set_facecolor(CARD_BG)
    ax.set_title(title, color=TEXT_COLOR, fontsize=14, fontweight='bold', pad=12)
    ax.set_xlabel(xlabel, color=TEXT_COLOR, fontsize=11)
    ax.set_ylabel(ylabel, color=TEXT_COLOR, fontsize=11)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(GRID_COLOR)
    ax.spines['bottom'].set_color(GRID_COLOR)
    ax.grid(axis='x', color=GRID_COLOR, alpha=0.3, linestyle='--')


# --------------------------------------------------
# Chart 1: Category (Sheep vs Goats)
# --------------------------------------------------

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.patch.set_facecolor(DARK_BG)
fig.suptitle('LMPR Livestock Auction Data — Category Breakdown',
             color=TEXT_COLOR, fontsize=18, fontweight='bold', y=0.98)

# 1a: Category pie
ax = axes[0, 0]
ax.set_facecolor(CARD_BG)
cat_counts = all_df['category'].value_counts()
wedges, texts, autotexts = ax.pie(
    cat_counts.values, labels=cat_counts.index,
    autopct='%1.1f%%', colors=[COLORS['primary'], COLORS['secondary']],
    textprops={'color': TEXT_COLOR, 'fontsize': 12},
    wedgeprops={'edgecolor': DARK_BG, 'linewidth': 2}
)
for t in autotexts:
    t.set_fontsize(11)
    t.set_fontweight('bold')
ax.set_title('Category: Sheep vs Goats', color=TEXT_COLOR, fontsize=14, fontweight='bold')

# 1b: Commodity breakdown
ax = axes[0, 1]
comm_counts = all_df['commodity'].value_counts()
bars = ax.barh(comm_counts.index, comm_counts.values, color=COLORS['palette'][:len(comm_counts)])
style_ax(ax, 'Commodity Type', xlabel='Number of Records')
for bar, val in zip(bars, comm_counts.values):
    ax.text(val + 30, bar.get_y() + bar.get_height()/2, f'{val:,}',
            va='center', color=TEXT_COLOR, fontsize=10)

# 1c: Top 10 Classes
ax = axes[1, 0]
class_counts = all_df['class'].value_counts().head(10)
bars = ax.barh(class_counts.index, class_counts.values, color=COLORS['palette'][:len(class_counts)])
style_ax(ax, 'Top 10 Animal Classes', xlabel='Number of Records')
for bar, val in zip(bars, class_counts.values):
    ax.text(val + 20, bar.get_y() + bar.get_height()/2, f'{val:,}',
            va='center', color=TEXT_COLOR, fontsize=9)

# 1d: Quality grades
ax = axes[1, 1]
grade_counts = all_df['quality_grade_name'].dropna().value_counts().head(8)
bars = ax.barh(grade_counts.index, grade_counts.values, color=COLORS['palette'][:len(grade_counts)])
style_ax(ax, 'Quality Grades', xlabel='Number of Records')
for bar, val in zip(bars, grade_counts.values):
    ax.text(val + 15, bar.get_y() + bar.get_height()/2, f'{val:,}',
            va='center', color=TEXT_COLOR, fontsize=9)

plt.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(os.path.join(OUTPUT_DIR, 'categories_breakdown.png'), dpi=150, facecolor=DARK_BG)
print("✔ Saved charts/categories_breakdown.png")
plt.close()


# --------------------------------------------------
# Chart 2: Geographic & Market Distribution
# --------------------------------------------------

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.patch.set_facecolor(DARK_BG)
fig.suptitle('LMPR Data — Geographic & Market Distribution',
             color=TEXT_COLOR, fontsize=18, fontweight='bold', y=0.98)

# 2a: State distribution
ax = axes[0, 0]
state_counts = all_df['market_location_state'].dropna().value_counts()
bars = ax.barh(state_counts.index, state_counts.values, color=COLORS['primary'])
style_ax(ax, 'Records by State', xlabel='Number of Records')
for bar, val in zip(bars, state_counts.values):
    ax.text(val + 15, bar.get_y() + bar.get_height()/2, f'{val:,}',
            va='center', color=TEXT_COLOR, fontsize=9)

# 2b: Price unit
ax = axes[0, 1]
ax.set_facecolor(CARD_BG)
pu_counts = all_df['price_unit'].dropna().value_counts()
wedges, texts, autotexts = ax.pie(
    pu_counts.values, labels=pu_counts.index,
    autopct='%1.1f%%', colors=[COLORS['accent'], COLORS['warm']],
    textprops={'color': TEXT_COLOR, 'fontsize': 12},
    wedgeprops={'edgecolor': DARK_BG, 'linewidth': 2}
)
for t in autotexts:
    t.set_fontsize(11)
    t.set_fontweight('bold')
ax.set_title('Pricing Unit', color=TEXT_COLOR, fontsize=14, fontweight='bold')

# 2c: Records per slug
ax = axes[1, 0]
slug_counts = all_df['slug_id'].value_counts().sort_values(ascending=True)
bars = ax.barh([str(s) for s in slug_counts.index], slug_counts.values, color=COLORS['teal'], height=0.7)
style_ax(ax, 'Records per Report (Slug ID)', xlabel='Number of Records')
ax.tick_params(axis='y', labelsize=7)

# 2d: Market type
ax = axes[1, 1]
ax.set_facecolor(CARD_BG)
mt_counts = all_df['market_type_category'].dropna().value_counts()
wedges, texts, autotexts = ax.pie(
    mt_counts.values, labels=mt_counts.index,
    autopct='%1.1f%%', colors=[COLORS['primary'], COLORS['purple']],
    textprops={'color': TEXT_COLOR, 'fontsize': 12},
    wedgeprops={'edgecolor': DARK_BG, 'linewidth': 2}
)
for t in autotexts:
    t.set_fontsize(11)
    t.set_fontweight('bold')
ax.set_title('Market Type', color=TEXT_COLOR, fontsize=14, fontweight='bold')

plt.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(os.path.join(OUTPUT_DIR, 'geographic_market.png'), dpi=150, facecolor=DARK_BG)
print("✔ Saved charts/geographic_market.png")
plt.close()


# --------------------------------------------------
# Chart 3: Price Distribution
# --------------------------------------------------

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.patch.set_facecolor(DARK_BG)
fig.suptitle('LMPR Data — Price Distribution (Per Cwt)',
             color=TEXT_COLOR, fontsize=18, fontweight='bold', y=1.02)

cwt_df = all_df[all_df['price_unit'] == 'Per Cwt'].copy()
cwt_df['avg_price'] = pd.to_numeric(cwt_df['avg_price'], errors='coerce')

# 3a: Price by category
ax = axes[0]
ax.set_facecolor(CARD_BG)
for i, cat in enumerate(['Sheep', 'Goats']):
    subset = cwt_df[cwt_df['category'] == cat]['avg_price'].dropna()
    if not subset.empty:
        ax.hist(subset, bins=40, alpha=0.65, label=cat,
                color=[COLORS['primary'], COLORS['secondary']][i], edgecolor='none')
style_ax(ax, 'Average Price Distribution', xlabel='Price ($/cwt)', ylabel='Frequency')
ax.legend(facecolor=CARD_BG, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR)

# 3b: Price by commodity (box plot)
ax = axes[1]
ax.set_facecolor(CARD_BG)
commodities = cwt_df['commodity'].dropna().unique()
box_data = [cwt_df[cwt_df['commodity'] == c]['avg_price'].dropna().values for c in commodities]
box_data = [d for d in box_data if len(d) > 0]
commodities = [c for c, d in zip(commodities, [cwt_df[cwt_df['commodity'] == c]['avg_price'].dropna().values for c in commodities]) if len(d) > 0]

bp = ax.boxplot(box_data, labels=[c.replace('Sheep/Lambs', 'S/L').replace('Goats', 'G') for c in commodities],
                patch_artist=True, vert=True)
for patch, color in zip(bp['boxes'], COLORS['palette']):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
for median in bp['medians']:
    median.set_color(TEXT_COLOR)
style_ax(ax, 'Price by Commodity Type', xlabel='Commodity', ylabel='Price ($/cwt)')
ax.tick_params(axis='x', rotation=20)

plt.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, 'price_distribution.png'), dpi=150, facecolor=DARK_BG)
print("✔ Saved charts/price_distribution.png")
plt.close()


# --------------------------------------------------
# Summary Stats
# --------------------------------------------------

print(f"""
{'='*60}
LMPR DATA SUMMARY
{'='*60}
Total Records:     {len(all_df):,}
Report Files:      {len(files)}
Date Range:        {all_df['report_date'].min()} → {all_df['report_date'].max()}
States Covered:    {all_df['market_location_state'].nunique()}
Unique Markets:    {all_df['market_location_name'].nunique()}
{'='*60}

COLUMN DEFINITIONS:
{'─'*60}
REPORT METADATA
  report_date          Date the auction/report occurred
  published_date       Date/time the report was published to USDA
  office_name/state    USDA office responsible for the report
  slug_id / slug_name  Unique report identifier in MARS API
  report_title         Full name of the auction report
  final_ind            Whether this is the Final or Preliminary report

MARKET INFO
  market_type          Type of market (Auction Livestock)
  market_type_category Auction vs Summary (individual auction vs weekly rollup)
  market_location_*    Physical auction location (name, city, state)

ANIMAL CLASSIFICATION
  group                Always "Livestock" in this dataset
  category             Top-level: Sheep or Goats
  commodity            Purpose: Slaughter, Feeder, or Replacement × Sheep/Goats
  class                Specific animal type (Kids, Hair Breeds, Ewes, Bucks, etc.)

GRADING & DESCRIPTION
  quality_grade_name   USDA quality grade (Selection 1-3, Choice, Good, Utility, Cull)
  frame                Body frame size (usually N/A for small ruminants)
  muscle_grade         Muscling score (usually N/A)
  lot_desc             Special lot descriptors (Pygmies, Yearlings, Fancy, etc.)

PRICING
  price_unit           Per Cwt (per 100 lbs) or Per Unit (per head)
  avg_price            Average sale price
  avg_price_min/max    Price range for the lot
  freight              Delivery terms (F.O.B. = buyer arranges transport)

WEIGHT & VOLUME
  avg_weight           Average animal weight (lbs)
  avg_weight_min/max   Weight range
  weight_break_low/high Weight bracket for the price quote
  head_count           Number of animals in the lot
  receipts             Total animals at this auction
  receipts_week_ago    Total animals at last week's auction
  receipts_year_ago    Total animals at same auction last year

NARRATIVE
  comments_commodity   Commodity-specific notes
  report_narrative     Full market commentary from the reporter
{'='*60}
""")
