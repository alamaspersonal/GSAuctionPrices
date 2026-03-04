import { useState } from 'react';
import { calculateProfitability } from '../hooks/useAuctionData';

export default function ProfitCalculator({ entry, onClose }) {
  const [inputs, setInputs] = useState({
    purchase_price_per_head: entry?.price_per_head || 200,
    purchase_weight: entry?.avg_weight || 60,
    target_sell_weight: 120,
    feed_cost_per_lb_gain: 0.45,
    mortality_pct: 3.0,
  });
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleCalculate = async () => {
    setLoading(true);
    try {
      const data = await calculateProfitability(inputs, {
        species: entry?.species,
        animal_class: entry?.animal_class,
      });
      setResults(data);
    } catch (err) {
      console.error('Profitability calc error:', err);
    } finally {
      setLoading(false);
    }
  };

  const updateInput = (key, value) => {
    setInputs(prev => ({ ...prev, [key]: Number(value) }));
  };

  return (
    <div className="detail-overlay" onClick={onClose}>
      <div className="detail-panel" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 480 }}>
        <div className="detail-header">
          <h2 style={{ fontSize: '1.125rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
            🧮 Break-Even Calculator
          </h2>
          <button className="detail-close" onClick={onClose}>✕</button>
        </div>

        <div className="detail-section">
          <div className="profit-input-group">
            <label>Purchase Price ($/head)</label>
            <input
              type="number" step="0.01"
              value={inputs.purchase_price_per_head}
              onChange={(e) => updateInput('purchase_price_per_head', e.target.value)}
            />
          </div>
          <div className="profit-input-group">
            <label>Purchase Weight (lbs)</label>
            <input
              type="number" step="1"
              value={inputs.purchase_weight}
              onChange={(e) => updateInput('purchase_weight', e.target.value)}
            />
          </div>

          <div style={{ marginTop: 'var(--space-md)' }}>
            <div className="range-slider-container">
              <div className="range-label">
                <span>Target Sell Weight</span>
                <span className="range-value">{inputs.target_sell_weight} lbs</span>
              </div>
              <input
                type="range" min={inputs.purchase_weight} max={300} step={5}
                value={inputs.target_sell_weight}
                onChange={(e) => updateInput('target_sell_weight', e.target.value)}
              />
            </div>
          </div>

          <div style={{ marginTop: 'var(--space-sm)' }}>
            <div className="range-slider-container">
              <div className="range-label">
                <span>Feed Cost per lb of Gain</span>
                <span className="range-value">${inputs.feed_cost_per_lb_gain.toFixed(2)}</span>
              </div>
              <input
                type="range" min={0.10} max={1.50} step={0.05}
                value={inputs.feed_cost_per_lb_gain}
                onChange={(e) => updateInput('feed_cost_per_lb_gain', e.target.value)}
              />
            </div>
          </div>

          <div style={{ marginTop: 'var(--space-sm)' }}>
            <div className="range-slider-container">
              <div className="range-label">
                <span>Mortality / Shrink %</span>
                <span className="range-value">{inputs.mortality_pct}%</span>
              </div>
              <input
                type="range" min={0} max={15} step={1}
                value={inputs.mortality_pct}
                onChange={(e) => updateInput('mortality_pct', e.target.value)}
              />
            </div>
          </div>

          <button
            className="btn-primary"
            style={{ width: '100%', marginTop: 'var(--space-md)' }}
            onClick={handleCalculate}
            disabled={loading}
          >
            {loading ? 'Calculating...' : 'Calculate Break-Even'}
          </button>
        </div>

        {results && (
          <div className="detail-section">
            <div className="profit-results">
              <div className="profit-row">
                <span className="label">Weight Gain</span>
                <span className="value">{results.weight_gain} lbs</span>
              </div>
              <div className="profit-row">
                <span className="label">Feed Cost</span>
                <span className="value">${results.feed_cost_total?.toFixed(2)}</span>
              </div>
              <div className="profit-row">
                <span className="label">Shrink / Mortality</span>
                <span className="value">${results.shrink_loss?.toFixed(2)}</span>
              </div>
              <div className="profit-row total">
                <span className="label">Total Investment</span>
                <span className="value">${results.total_investment?.toFixed(2)}</span>
              </div>
              <div className="profit-row" style={{ marginTop: 'var(--space-sm)' }}>
                <span className="label">Break-Even Price</span>
                <span className="value" style={{ fontFamily: 'var(--font-mono)' }}>
                  ${results.break_even_per_lb?.toFixed(2)}/lb
                  <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}> (${results.break_even_per_cwt?.toFixed(0)}/cwt)</span>
                </span>
              </div>

              {results.current_market_avg_per_lb != null && (
                <>
                  <div className="profit-row" style={{ marginTop: 'var(--space-sm)', paddingTop: 'var(--space-sm)', borderTop: '1px solid var(--border-light)' }}>
                    <span className="label">Current Market Avg</span>
                    <span className="value">${results.current_market_avg_per_lb?.toFixed(2)}/lb</span>
                  </div>
                  <div className="profit-row margin">
                    <span className="label" style={{ fontWeight: 600 }}>Estimated Margin</span>
                    <span className={`value ${results.margin_per_head >= 0 ? 'positive' : 'negative'}`}>
                      {results.margin_per_head >= 0 ? '+' : ''}${results.margin_per_head?.toFixed(2)}/hd
                      ({results.margin_pct >= 0 ? '+' : ''}{results.margin_pct?.toFixed(1)}%)
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
