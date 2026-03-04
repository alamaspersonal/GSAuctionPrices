import { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Area, ScatterChart, Scatter, ZAxis, Legend,
} from 'recharts';
import { fetchTrends, fetchScatter } from '../hooks/useAuctionData';

export default function TrendChart({ filters }) {
  const [tab, setTab] = useState('trend');
  const [trendData, setTrendData] = useState([]);
  const [scatterData, setScatterData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        if (tab === 'trend') {
          const data = await fetchTrends({
            species: filters.species,
            commodity: null,
            animal_class: filters.animal_class,
            weight_min: filters.weight_min > 0 ? filters.weight_min : null,
            weight_max: filters.weight_max < 350 ? filters.weight_max : null,
            period: 90,
          });
          setTrendData(data);
        } else {
          const data = await fetchScatter({
            species: filters.species,
            date_from: '2024-01-01',
            limit: 1000,
          });
          setScatterData(data);
        }
      } catch (err) {
        console.error('Chart data error:', err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [tab, filters.species, filters.animal_class, filters.weight_min, filters.weight_max]);

  const commodityColor = (commodity) => {
    if (commodity?.includes('Slaughter')) return 'var(--color-slaughter)';
    if (commodity?.includes('Feeder')) return 'var(--color-feeder)';
    if (commodity?.includes('Replacement')) return 'var(--color-breeding)';
    return 'var(--olive)';
  };

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border-light)',
        borderRadius: 'var(--radius-sm)', padding: '8px 12px', fontSize: '0.8rem',
        boxShadow: 'var(--shadow-md)',
      }}>
        {tab === 'trend' ? (
          <>
            <div style={{ fontWeight: 600 }}>{d.week_label}</div>
            <div style={{ fontFamily: 'var(--font-mono)' }}>Avg: ${d.avg_price_per_lb?.toFixed(2)}/lb</div>
            <div style={{ color: 'var(--text-muted)' }}>{d.lot_count} lots · {d.head_count} hd</div>
            {d.price_min != null && <div style={{ color: 'var(--text-muted)' }}>Range: ${d.price_min?.toFixed(2)} – ${d.price_max?.toFixed(2)}</div>}
          </>
        ) : (
          <>
            <div style={{ fontWeight: 600 }}>{d.animal_class}</div>
            <div style={{ fontFamily: 'var(--font-mono)' }}>{d.avg_weight} lbs @ ${d.price_per_lb?.toFixed(2)}/lb</div>
            <div style={{ color: 'var(--text-muted)' }}>{d.market_name}</div>
            <div style={{ color: 'var(--text-muted)' }}>{d.head_count} hd · {d.report_date}</div>
          </>
        )}
      </div>
    );
  };

  // Split scatter data by commodity for color coding
  const slaughterData = scatterData.filter(d => d.commodity?.includes('Slaughter'));
  const feederData = scatterData.filter(d => d.commodity?.includes('Feeder'));
  const replData = scatterData.filter(d => d.commodity?.includes('Replacement'));

  return (
    <div className="chart-container">
      <div className="tabs">
        <button className={`tab-btn ${tab === 'trend' ? 'active' : ''}`} onClick={() => setTab('trend')}>
          📈 Price Trend
        </button>
        <button className={`tab-btn ${tab === 'scatter' ? 'active' : ''}`} onClick={() => setTab('scatter')}>
          📊 Price vs Weight
        </button>
      </div>

      {loading ? (
        <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
          Loading chart data...
        </div>
      ) : tab === 'trend' ? (
        <>
          <div className="chart-title">Weekly Average Price per Lb (Last 90 Days)</div>
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={trendData} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis
                dataKey="week_label" tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
                tickFormatter={(v) => v?.split('-W')?.[1] ? `W${v.split('-W')[1]}` : v}
              />
              <YAxis
                tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
                tickFormatter={(v) => `$${v.toFixed(2)}`}
                domain={['auto', 'auto']}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone" dataKey="price_max"
                stroke="none" fill="var(--khaki)" fillOpacity={0.2}
              />
              <Area
                type="monotone" dataKey="price_min"
                stroke="none" fill="var(--bg-page)" fillOpacity={1}
              />
              <Line
                type="monotone" dataKey="avg_price_per_lb"
                stroke="var(--olive)" strokeWidth={2.5}
                dot={{ r: 4, fill: 'var(--olive)', stroke: 'var(--bg-card)', strokeWidth: 2 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </>
      ) : (
        <>
          <div className="chart-title">Price per Lb vs Weight — Colored by Commodity</div>
          <ResponsiveContainer width="100%" height={320}>
            <ScatterChart margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis
                dataKey="avg_weight" type="number" name="Weight"
                tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
                label={{ value: 'Weight (lbs)', position: 'insideBottom', offset: -5, fontSize: 11, fill: 'var(--text-muted)' }}
              />
              <YAxis
                dataKey="price_per_lb" type="number" name="Price"
                tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
                tickFormatter={(v) => `$${v.toFixed(2)}`}
                label={{ value: '$/lb', angle: -90, position: 'insideLeft', fontSize: 11, fill: 'var(--text-muted)' }}
              />
              <ZAxis dataKey="head_count" range={[20, 200]} name="Head" />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Scatter name="Slaughter" data={slaughterData} fill="#717744" fillOpacity={0.6} />
              <Scatter name="Feeder" data={feederData} fill="#5B8A72" fillOpacity={0.6} />
              <Scatter name="Replacement" data={replData} fill="#766153" fillOpacity={0.6} />
            </ScatterChart>
          </ResponsiveContainer>
        </>
      )}
    </div>
  );
}
