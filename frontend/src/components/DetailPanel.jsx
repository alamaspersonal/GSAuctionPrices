export default function DetailPanel({ entry, onClose, getDisplayPrice, getPriceUnitLabel, onOpenCalculator }) {
  if (!entry) return null;

  const formatDate = (d) => {
    if (!d) return '';
    try {
      const date = new Date(d);
      return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return d;
    }
  };

  const intentLabel = {
    meat: 'Slaughter',
    feeder: 'Feeder',
    breeding: 'Replacement',
  }[entry.buyer_intent] || '';

  const badgeClass = entry.buyer_intent || 'meat';

  return (
    <div className="detail-overlay" onClick={onClose}>
      <div className="detail-panel" onClick={(e) => e.stopPropagation()}>
        <div className="detail-header">
          <div>
            <span className={`card-badge ${badgeClass}`} style={{ marginBottom: 8, display: 'inline-flex' }}>
              {intentLabel} · {entry.species}
            </span>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: 8 }}>
              {entry.animal_class}
            </h2>
            {entry.quality_grade && (
              <div style={{ marginTop: 4 }}>
                <span className="card-grade">{entry.quality_grade}</span>
                {entry.dressing && <span className="card-grade" style={{ marginLeft: 4 }}>{entry.dressing} Dressing</span>}
                {entry.frame && <span className="card-grade" style={{ marginLeft: 4 }}>{entry.frame} Frame</span>}
              </div>
            )}
          </div>
          <button className="detail-close" onClick={onClose}>✕</button>
        </div>

        {/* Price Section */}
        <div className="detail-section">
          <div className="detail-section-title">Pricing</div>
          <div className="detail-price-big">
            {getDisplayPrice(entry)}<span style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--text-muted)' }}>{getPriceUnitLabel()}</span>
          </div>
          {entry.price_min != null && entry.price_max != null && (
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: 4 }}>
              Range: ${entry.price_min.toFixed(2)} – ${entry.price_max.toFixed(2)} {entry.price_unit === 'Per Cwt' ? '/cwt' : '/hd'}
            </div>
          )}
          <div className="detail-price-conversions">
            {entry.price_per_lb != null && `≈ $${entry.price_per_lb.toFixed(2)}/lb`}
            {entry.price_per_head != null && ` · ≈ $${entry.price_per_head.toFixed(0)}/hd`}
            {entry.price_per_cwt != null && ` · $${entry.price_per_cwt.toFixed(2)}/cwt`}
          </div>
        </div>

        {/* Animal Section */}
        <div className="detail-section">
          <div className="detail-section-title">Animal Details</div>
          <div className="detail-data-grid">
            <div className="detail-data-item">
              <label>Weight</label>
              <div className="value">
                {entry.avg_weight != null ? `${entry.avg_weight} lbs` : '—'}
                {entry.weight_min != null && entry.weight_max != null && (
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}> ({entry.weight_min}–{entry.weight_max})</span>
                )}
              </div>
            </div>
            <div className="detail-data-item">
              <label>Head Count</label>
              <div className="value">{entry.head_count ?? '—'}</div>
            </div>
            <div className="detail-data-item">
              <label>Weight Bracket</label>
              <div className="value">
                {entry.weight_break_low != null && entry.weight_break_high != null
                  ? `${entry.weight_break_low}–${entry.weight_break_high} lbs`
                  : '—'}
              </div>
            </div>
            <div className="detail-data-item">
              <label>Breed Type</label>
              <div className="value">{entry.breed_type || '—'}</div>
            </div>
            {entry.lot_desc && (
              <div className="detail-data-item">
                <label>Lot Notes</label>
                <div className="value">{entry.lot_desc}</div>
              </div>
            )}
            {entry.age && (
              <div className="detail-data-item">
                <label>Age</label>
                <div className="value">{entry.age}</div>
              </div>
            )}
          </div>
        </div>

        {/* Market Section */}
        <div className="detail-section">
          <div className="detail-section-title">Market</div>
          <div className="detail-data-grid">
            <div className="detail-data-item" style={{ gridColumn: '1 / -1' }}>
              <label>Auction Yard</label>
              <div className="value">📍 {entry.market_name} — {entry.market_city}, {entry.market_state}</div>
            </div>
            <div className="detail-data-item">
              <label>Report Date</label>
              <div className="value">📅 {formatDate(entry.report_date)}</div>
            </div>
            <div className="detail-data-item">
              <label>Report</label>
              <div className="value">{entry.market_type === 'Summary' ? 'Weekly Summary' : 'Auction'}</div>
            </div>
            <div className="detail-data-item">
              <label>Receipts</label>
              <div className="value">
                {entry.receipts ?? '—'} hd
              </div>
            </div>
            <div className="detail-data-item">
              <label>Last Week</label>
              <div className="value">{entry.receipts_week_ago ?? '—'} hd</div>
            </div>
            <div className="detail-data-item">
              <label>Last Year</label>
              <div className="value">{entry.receipts_year_ago ?? '—'} hd</div>
            </div>
          </div>
        </div>

        {/* Narrative */}
        {entry.narrative && (
          <div className="detail-section">
            <div className="detail-section-title">Market Narrative</div>
            <div className="detail-narrative">{entry.narrative}</div>
          </div>
        )}

        {/* Actions */}
        <div className="detail-actions">
          <button className="btn-primary" onClick={() => onOpenCalculator && onOpenCalculator(entry)}>
            🧮 Profitability Calculator
          </button>
          <button className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
