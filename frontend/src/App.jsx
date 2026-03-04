import { useState } from 'react';
import './index.css';
import { useAuctionData } from './hooks/useAuctionData';
import FilterPanel from './components/FilterPanel';
import AuctionCard from './components/AuctionCard';
import DetailPanel from './components/DetailPanel';
import TrendChart from './components/TrendChart';
import ProfitCalculator from './components/ProfitCalculator';
import SellerView from './components/SellerView';

function App() {
  const {
    entries, count, totalPages, loading, suggestions, summary,
    classes, states, grades, markets,
    filters, updateFilter, resetFilters, setPage,
    priceUnit, setPriceUnit, getDisplayPrice, getPriceUnitLabel,
  } = useAuctionData();

  const [mode, setMode] = useState('buyer'); // buyer | seller
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [calculatorEntry, setCalculatorEntry] = useState(null);
  const [showCharts, setShowCharts] = useState(false);

  return (
    <div className="app-layout">
      {/* Navigation */}
      <nav className="nav-bar">
        <div className="nav-brand">
          🐑 <span>GS</span>AuctionPrices
        </div>

        <div className="nav-controls">
          <div className="mode-toggle">
            <button className={mode === 'buyer' ? 'active' : ''} onClick={() => setMode('buyer')}>
              Buyer
            </button>
            <button className={mode === 'seller' ? 'active' : ''} onClick={() => setMode('seller')}>
              Seller
            </button>
          </div>

          <div className="unit-toggle">
            <button className={priceUnit === 'cwt' ? 'active' : ''} onClick={() => setPriceUnit('cwt')}>
              $/Cwt
            </button>
            <button className={priceUnit === 'lb' ? 'active' : ''} onClick={() => setPriceUnit('lb')}>
              $/Lb
            </button>
            <button className={priceUnit === 'head' ? 'active' : ''} onClick={() => setPriceUnit('head')}>
              $/Hd
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="content-layout">
        {/* Left Sidebar — Filters (Buyer mode only) */}
        {mode === 'buyer' && (
          <FilterPanel
            filters={filters}
            updateFilter={updateFilter}
            resetFilters={resetFilters}
            classes={classes}
            states={states}
            grades={grades}
          />
        )}

        {/* Main Content Area */}
        <main className="main-content">
          {/* Summary Widgets */}
          {summary && (
            <div className="summary-grid">
              {summary.widgets.map((w, i) => (
                <div className="summary-widget" key={i}>
                  <div className="widget-label">{w.label}</div>
                  <div className="widget-value">{w.value}</div>
                  {w.sub_label && <div className="widget-sub">{w.sub_label}</div>}
                  {w.trend_pct != null && (
                    <div className={`widget-trend ${w.trend_direction || ''}`}>
                      {w.trend_direction === 'up' ? '↑' : w.trend_direction === 'down' ? '↓' : '→'}
                      {' '}{Math.abs(w.trend_pct).toFixed(1)}%
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {mode === 'buyer' ? (
            <>
              {/* Tabs: Listings / Charts */}
              <div className="tabs">
                <button
                  className={`tab-btn ${!showCharts ? 'active' : ''}`}
                  onClick={() => setShowCharts(false)}
                >
                  📋 Listings
                </button>
                <button
                  className={`tab-btn ${showCharts ? 'active' : ''}`}
                  onClick={() => setShowCharts(true)}
                >
                  📊 Trends
                </button>
              </div>

              {showCharts ? (
                <TrendChart filters={filters} />
              ) : (
                <>
                  {/* Results Bar */}
                  <div className="results-bar">
                    <span className="results-count">
                      <strong>{count.toLocaleString()}</strong> lots found
                    </span>
                    <select
                      className="sort-select"
                      value={`${filters.sort_by}-${filters.sort_dir}`}
                      onChange={(e) => {
                        const [sortBy, sortDir] = e.target.value.split('-');
                        updateFilter('sort_by', sortBy);
                        setTimeout(() => updateFilter('sort_dir', sortDir), 0);
                      }}
                    >
                      <option value="report_date-desc">Newest First</option>
                      <option value="report_date-asc">Oldest First</option>
                      <option value="price_per_lb-asc">Lowest $/lb</option>
                      <option value="price_per_lb-desc">Highest $/lb</option>
                      <option value="avg_weight-asc">Lightest</option>
                      <option value="avg_weight-desc">Heaviest</option>
                      <option value="head_count-desc">Most Head</option>
                    </select>
                  </div>

                  {/* Loading State */}
                  {loading ? (
                    <div className="card-grid">
                      {Array.from({ length: 8 }).map((_, i) => (
                        <div key={i} className="auction-card" style={{ minHeight: 180 }}>
                          <div className="loading-skeleton" style={{ width: '40%', height: 14 }} />
                          <div className="loading-skeleton" style={{ width: '60%', height: 20, marginTop: 12 }} />
                          <div className="loading-skeleton" style={{ width: '30%', height: 28, marginTop: 12 }} />
                          <div className="loading-skeleton" style={{ width: '80%', height: 14, marginTop: 12 }} />
                          <div className="loading-skeleton" style={{ width: '100%', height: 14, marginTop: 12 }} />
                        </div>
                      ))}
                    </div>
                  ) : entries.length > 0 ? (
                    <>
                      <div className="card-grid">
                        {entries.map((entry) => (
                          <AuctionCard
                            key={entry.id}
                            entry={entry}
                            getDisplayPrice={getDisplayPrice}
                            getPriceUnitLabel={getPriceUnitLabel}
                            onClick={setSelectedEntry}
                          />
                        ))}
                      </div>

                      {/* Pagination */}
                      {totalPages > 1 && (
                        <div className="pagination">
                          <button
                            disabled={filters.page <= 1}
                            onClick={() => setPage(filters.page - 1)}
                          >
                            ← Prev
                          </button>
                          <span className="page-info">
                            Page {filters.page} of {totalPages}
                          </span>
                          <button
                            disabled={filters.page >= totalPages}
                            onClick={() => setPage(filters.page + 1)}
                          >
                            Next →
                          </button>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="empty-state">
                      <div className="empty-icon">🔍</div>
                      <h3>No lots found</h3>
                      <p>Try adjusting your filters to see more results.</p>

                      {suggestions && (
                        <div className="suggestion-chips">
                          {suggestions.weight_expanded && (
                            <button
                              className="suggestion-chip"
                              onClick={() => {
                                updateFilter('weight_min', suggestions.weight_expanded.range[0]);
                                setTimeout(() => updateFilter('weight_max', suggestions.weight_expanded.range[1]), 0);
                              }}
                            >
                              Expand weight to {suggestions.weight_expanded.range[0]}–{suggestions.weight_expanded.range[1]} lbs ({suggestions.weight_expanded.count} lots)
                            </button>
                          )}
                          {suggestions.states_nearby?.map(s => (
                            <button
                              key={s.state}
                              className="suggestion-chip"
                              onClick={() => updateFilter('state', s.state)}
                            >
                              Try {s.state} ({s.count} lots)
                            </button>
                          ))}
                          {suggestions.time_expanded && (
                            <button
                              className="suggestion-chip"
                              onClick={() => updateFilter('date_from', null)}
                            >
                              Show all dates ({suggestions.time_expanded.count} lots)
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </>
          ) : (
            /* Seller Mode */
            <SellerView />
          )}
        </main>
      </div>

      {/* Detail Panel */}
      {selectedEntry && (
        <DetailPanel
          entry={selectedEntry}
          onClose={() => setSelectedEntry(null)}
          getDisplayPrice={getDisplayPrice}
          getPriceUnitLabel={getPriceUnitLabel}
          onOpenCalculator={(entry) => {
            setSelectedEntry(null);
            setCalculatorEntry(entry);
          }}
        />
      )}

      {/* Profitability Calculator */}
      {calculatorEntry && (
        <ProfitCalculator
          entry={calculatorEntry}
          onClose={() => setCalculatorEntry(null)}
        />
      )}
    </div>
  );
}

export default App;
