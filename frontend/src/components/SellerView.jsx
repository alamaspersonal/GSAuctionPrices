import { useState, useEffect } from 'react';
import { fetchCompare } from '../hooks/useAuctionData';

export default function SellerView() {
  const [species, setSpecies] = useState('Goats');
  const [animalClass, setAnimalClass] = useState('Kids');
  const [weightTarget, setWeightTarget] = useState(60);
  const [period, setPeriod] = useState(30);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const classOptions = {
    Goats: ['Kids', 'Nannies/Does', 'Bucks/Billies', 'Wethers', 'Wether Kids'],
    Sheep: ['Hair Breeds', 'Wooled & Shorn', 'Hair Ewes', 'Ewes', 'Hair Bucks', 'Lambs'],
  };

  const handleSearch = async () => {
    setLoading(true);
    try {
      const data = await fetchCompare({
        species,
        animal_class: animalClass,
        weight_min: Math.max(0, weightTarget - 20),
        weight_max: weightTarget + 20,
        period,
      });
      setResults(data);
    } catch (err) {
      console.error('Compare error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSearch();
  }, []);

  return (
    <div>
      <div className="seller-form">
        <h3>📍 Find Best Markets for Your Animals</h3>
        <div className="seller-form-row">
          <select value={species} onChange={(e) => {
            setSpecies(e.target.value);
            setAnimalClass(classOptions[e.target.value][0]);
          }}>
            <option value="Goats">🐐 Goats</option>
            <option value="Sheep">🐑 Sheep</option>
          </select>
          <select value={animalClass} onChange={(e) => setAnimalClass(e.target.value)}>
            {classOptions[species].map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <div className="range-slider-container">
          <div className="range-label">
            <span>Approx. Weight</span>
            <span className="range-value">~{weightTarget} lbs</span>
          </div>
          <input
            type="range" min={10} max={300} step={10}
            value={weightTarget}
            onChange={(e) => setWeightTarget(Number(e.target.value))}
          />
        </div>

        <div style={{ display: 'flex', gap: 'var(--space-sm)', marginTop: 'var(--space-sm)' }}>
          {[14, 30, 90].map(d => (
            <button
              key={d}
              className={`chip ${period === d ? 'active' : ''}`}
              onClick={() => setPeriod(d)}
            >
              {d}d
            </button>
          ))}
        </div>

        <button
          className="btn-primary"
          style={{ width: '100%', marginTop: 'var(--space-md)' }}
          onClick={handleSearch}
          disabled={loading}
        >
          {loading ? 'Searching...' : 'Find Best Markets →'}
        </button>
      </div>

      {results.length > 0 ? (
        <div className="chart-container" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="compare-table">
            <thead>
              <tr>
                <th>Auction Yard</th>
                <th>State</th>
                <th>Avg $/lb</th>
                <th>Avg $/Hd</th>
                <th>Lots</th>
                <th>Head</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 500 }}>{r.market_name}</td>
                  <td>{r.market_state}</td>
                  <td className="price-cell">
                    {r.avg_price_per_lb != null ? `$${r.avg_price_per_lb.toFixed(2)}` : '—'}
                  </td>
                  <td className="price-cell">
                    {r.avg_price_per_head != null ? `$${r.avg_price_per_head.toFixed(0)}` : '—'}
                  </td>
                  <td>{r.lot_count}</td>
                  <td>{r.head_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : !loading ? (
        <div className="empty-state">
          <div className="empty-icon">📊</div>
          <h3>No market data found</h3>
          <p>Try adjusting the weight range or time period.</p>
        </div>
      ) : null}
    </div>
  );
}
