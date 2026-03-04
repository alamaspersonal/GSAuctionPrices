export default function AuctionCard({ entry, getDisplayPrice, getPriceUnitLabel, onClick }) {
  const intentClass = entry.buyer_intent ? `intent-${entry.buyer_intent}` : 'intent-meat';
  const badgeClass = entry.buyer_intent || 'meat';
  const intentLabel = {
    meat: 'Slaughter',
    feeder: 'Feeder',
    breeding: 'Replacement',
  }[entry.buyer_intent] || 'Other';

  const formatDate = (d) => {
    if (!d) return '';
    try {
      const date = new Date(d);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return d;
    }
  };

  const receiptChange = entry.receipts && entry.receipts_week_ago
    ? Math.round(((entry.receipts - entry.receipts_week_ago) / entry.receipts_week_ago) * 100)
    : null;

  return (
    <div className={`auction-card ${intentClass}`} onClick={() => onClick(entry)}>
      <div className="card-header">
        <span className={`card-badge ${badgeClass}`}>{intentLabel}</span>
        <span className="card-location">
          {entry.market_city && `${entry.market_city}, `}{entry.market_state}
        </span>
      </div>

      <div className="card-title">{entry.animal_class || 'Unknown'}</div>
      {entry.quality_grade && (
        <span className="card-grade">{entry.quality_grade}</span>
      )}

      <div className="card-price-row">
        <span className="card-price">{getDisplayPrice(entry)}</span>
        <span className="card-price-unit">{getPriceUnitLabel()}</span>
      </div>

      <div className="card-stats">
        {entry.avg_weight != null && (
          <div className="card-stat">
            <span className="card-stat-value">{entry.avg_weight} lbs</span>
            <span className="card-stat-label">avg weight</span>
          </div>
        )}
        {entry.head_count != null && (
          <div className="card-stat">
            <span className="card-stat-value">{entry.head_count} hd</span>
            <span className="card-stat-label">head count</span>
          </div>
        )}
        {entry.price_min != null && entry.price_max != null && (
          <div className="card-stat">
            <span className="card-stat-value">${entry.price_min}–{entry.price_max}</span>
            <span className="card-stat-label">range</span>
          </div>
        )}
      </div>

      {entry.price_per_lb != null && entry.price_per_head != null && (
        <div className="card-derived">
          ≈ ${entry.price_per_lb.toFixed(2)}/lb · ≈ ${entry.price_per_head.toFixed(0)}/hd
        </div>
      )}

      <div className="card-footer">
        <span className="market-name">{entry.market_name}</span>
        <span>
          {formatDate(entry.report_date)}
          {entry.receipts != null && (
            <span className="receipts-badge">
              {' · '}{entry.receipts} rcpts
              {receiptChange != null && (
                <span style={{ color: receiptChange >= 0 ? 'var(--color-up)' : 'var(--color-down)' }}>
                  {' '}{receiptChange >= 0 ? '↑' : '↓'}{Math.abs(receiptChange)}%
                </span>
              )}
            </span>
          )}
        </span>
      </div>
    </div>
  );
}
