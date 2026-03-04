import { useState } from 'react';

export default function FilterPanel({
  filters, updateFilter, resetFilters,
  classes, states, grades,
}) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const intents = [
    { key: 'meat', icon: '🥩', label: 'Meat Market', sub: 'Slaughter' },
    { key: 'feeder', icon: '🌱', label: 'Feeder / Grow', sub: 'Feeder' },
    { key: 'breeding', icon: '🐏', label: 'Breeding Stock', sub: 'Replacement' },
  ];

  const speciesOptions = [
    { key: null, label: 'Both' },
    { key: 'Sheep', label: '🐑 Sheep' },
    { key: 'Goats', label: '🐐 Goats' },
  ];

  const topStates = states.slice(0, 8);

  return (
    <div className="filter-sidebar">
      {/* Intent */}
      <div className="filter-section">
        <div className="filter-section-title">Purpose</div>
        <div className="intent-buttons">
          {intents.map((i) => (
            <button
              key={i.key}
              className={`intent-btn ${filters.intent === i.key ? 'active' : ''}`}
              onClick={() => updateFilter('intent', filters.intent === i.key ? null : i.key)}
            >
              <span className="intent-icon">{i.icon}</span>
              <span>{i.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Species */}
      <div className="filter-section">
        <div className="filter-section-title">Species</div>
        <div className="species-toggle">
          {speciesOptions.map((s) => (
            <button
              key={s.key || 'both'}
              className={`species-btn ${filters.species === s.key ? 'active' : ''}`}
              onClick={() => updateFilter('species', s.key)}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Weight */}
      <div className="filter-section">
        <div className="filter-section-title">Weight Range</div>
        <div className="range-slider-container">
          <div className="range-label">
            <span>Min</span>
            <span className="range-value">{filters.weight_min} lbs</span>
          </div>
          <input
            type="range" min={0} max={350} step={10}
            value={filters.weight_min}
            onChange={(e) => updateFilter('weight_min', Number(e.target.value))}
          />
        </div>
        <div className="range-slider-container">
          <div className="range-label">
            <span>Max</span>
            <span className="range-value">{filters.weight_max} lbs</span>
          </div>
          <input
            type="range" min={0} max={350} step={10}
            value={filters.weight_max}
            onChange={(e) => updateFilter('weight_max', Number(e.target.value))}
          />
        </div>
      </div>

      {/* States */}
      <div className="filter-section">
        <div className="filter-section-title">States</div>
        <div className="chip-group">
          {topStates.map((s) => (
            <button
              key={s.code}
              className={`chip ${filters.state === s.code ? 'active' : ''}`}
              onClick={() => updateFilter('state', filters.state === s.code ? null : s.code)}
            >
              {s.code}
              <span className="chip-count">{s.count}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Advanced Toggle */}
      <button className="advanced-toggle" onClick={() => setShowAdvanced(!showAdvanced)}>
        {showAdvanced ? '▾' : '▸'} Advanced Filters
      </button>

      <div className={`advanced-filters ${showAdvanced ? 'expanded' : 'collapsed'}`}>
        {/* Classes */}
        <div className="filter-section">
          <div className="filter-section-title">Class</div>
          <div className="chip-group">
            {classes.slice(0, 12).map((c) => (
              <button
                key={c.name}
                className={`chip ${filters.animal_class === c.name ? 'active' : ''}`}
                onClick={() => updateFilter('animal_class', filters.animal_class === c.name ? null : c.name)}
              >
                {c.name}
                <span className="chip-count">{c.count}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Grades */}
        <div className="filter-section">
          <div className="filter-section-title">Quality Grade</div>
          <div className="chip-group">
            {grades.slice(0, 8).map((g) => (
              <button
                key={g.name}
                className={`chip ${filters.grade === g.name ? 'active' : ''}`}
                onClick={() => updateFilter('grade', filters.grade === g.name ? null : g.name)}
              >
                {g.name}
              </button>
            ))}
          </div>
        </div>

        {/* Breed type */}
        <div className="filter-section">
          <div className="filter-section-title">Breed Type</div>
          <div className="chip-group">
            {['Hair', 'Wooled'].map(bt => (
              <button
                key={bt}
                className={`chip ${filters.breed_type === bt ? 'active' : ''}`}
                onClick={() => updateFilter('breed_type', filters.breed_type === bt ? null : bt)}
              >
                {bt}
              </button>
            ))}
          </div>
        </div>

        {/* Lot descriptor */}
        <div className="filter-section">
          <div className="filter-section-title">Lot Type</div>
          <div className="chip-group">
            {['Pygmies', 'Yearlings', 'Fancy'].map(d => (
              <button
                key={d}
                className={`chip ${filters.lot_desc === d ? 'active' : ''}`}
                onClick={() => updateFilter('lot_desc', filters.lot_desc === d ? null : d)}
              >
                {d}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Reset */}
      <div style={{ marginTop: 'var(--space-lg)', paddingTop: 'var(--space-md)', borderTop: '1px solid var(--border-light)' }}>
        <button className="btn-secondary" style={{ width: '100%' }} onClick={resetFilters}>
          Reset All Filters
        </button>
      </div>
    </div>
  );
}
