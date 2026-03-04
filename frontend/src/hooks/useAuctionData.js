import { useState, useEffect, useCallback } from 'react';

const API_BASE = 'http://localhost:8000/api';

export function useAuctionData() {
  const [entries, setEntries] = useState([]);
  const [count, setCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState(null);
  const [summary, setSummary] = useState(null);
  const [classes, setClasses] = useState([]);
  const [states, setStates] = useState([]);
  const [grades, setGrades] = useState([]);
  const [markets, setMarkets] = useState([]);

  // Filter state
  const [filters, setFilters] = useState({
    species: null,
    intent: null,
    animal_class: null,
    breed_type: null,
    grade: null,
    weight_min: 0,
    weight_max: 350,
    state: null,
    lot_desc: null,
    sort_by: 'report_date',
    sort_dir: 'desc',
    page: 1,
    limit: 48,
  });

  const [priceUnit, setPriceUnit] = useState('cwt'); // cwt | lb | head

  // Fetch entries
  const fetchEntries = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.species) params.set('species', filters.species);
      if (filters.intent) params.set('intent', filters.intent);
      if (filters.animal_class) params.set('animal_class', filters.animal_class);
      if (filters.breed_type) params.set('breed_type', filters.breed_type);
      if (filters.grade) params.set('grade', filters.grade);
      if (filters.weight_min > 0) params.set('weight_min', filters.weight_min);
      if (filters.weight_max < 350) params.set('weight_max', filters.weight_max);
      if (filters.state) params.set('state', filters.state);
      if (filters.lot_desc) params.set('lot_desc', filters.lot_desc);
      params.set('sort_by', filters.sort_by);
      params.set('sort_dir', filters.sort_dir);
      params.set('page', filters.page);
      params.set('limit', filters.limit);

      const res = await fetch(`${API_BASE}/entries?${params}`);
      const data = await res.json();
      setEntries(data.results || []);
      setCount(data.count || 0);
      setTotalPages(data.total_pages || 1);
      setSuggestions(data.suggestions || null);
    } catch (err) {
      console.error('Failed to fetch entries:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Fetch summary
  const fetchSummary = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/analytics/summary?date_from=2024-01-01`);
      const data = await res.json();
      setSummary(data);
    } catch (err) {
      console.error('Failed to fetch summary:', err);
    }
  }, []);

  // Fetch meta for filter dropdowns
  const fetchMeta = useCallback(async () => {
    try {
      const [classRes, stateRes, gradeRes, marketRes] = await Promise.all([
        fetch(`${API_BASE}/analytics/meta/classes${filters.species ? `?species=${filters.species}` : ''}${filters.intent ? `${filters.species ? '&' : '?'}intent=${filters.intent}` : ''}`),
        fetch(`${API_BASE}/analytics/meta/states`),
        fetch(`${API_BASE}/analytics/meta/grades`),
        fetch(`${API_BASE}/analytics/meta/markets`),
      ]);
      const [classData, stateData, gradeData, marketData] = await Promise.all([
        classRes.json(), stateRes.json(), gradeRes.json(), marketRes.json(),
      ]);
      setClasses(classData.classes || []);
      setStates(stateData.states || []);
      setGrades(gradeData.grades || []);
      setMarkets(marketData.markets || []);
    } catch (err) {
      console.error('Failed to fetch meta:', err);
    }
  }, [filters.species, filters.intent]);

  useEffect(() => { fetchEntries(); }, [fetchEntries]);
  useEffect(() => { fetchSummary(); }, [fetchSummary]);
  useEffect(() => { fetchMeta(); }, [fetchMeta]);

  const updateFilter = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value, page: 1 }));
  };

  const resetFilters = () => {
    setFilters({
      species: null, intent: null, animal_class: null, breed_type: null,
      grade: null, weight_min: 0, weight_max: 350, state: null, lot_desc: null,
      sort_by: 'report_date', sort_dir: 'desc', page: 1, limit: 48,
    });
  };

  const setPage = (page) => {
    setFilters(prev => ({ ...prev, page }));
  };

  const getDisplayPrice = (entry) => {
    switch (priceUnit) {
      case 'lb':
        return entry.price_per_lb != null ? `$${entry.price_per_lb.toFixed(2)}` : '—';
      case 'head':
        return entry.price_per_head != null ? `$${entry.price_per_head.toFixed(0)}` : '—';
      case 'cwt':
      default:
        return entry.price_per_cwt != null ? `$${entry.price_per_cwt.toFixed(2)}` : (entry.avg_price != null ? `$${entry.avg_price.toFixed(2)}` : '—');
    }
  };

  const getPriceUnitLabel = () => {
    switch (priceUnit) {
      case 'lb': return '/lb';
      case 'head': return '/hd';
      case 'cwt':
      default: return '/cwt';
    }
  };

  return {
    entries, count, totalPages, loading, suggestions, summary,
    classes, states, grades, markets,
    filters, updateFilter, resetFilters, setPage,
    priceUnit, setPriceUnit, getDisplayPrice, getPriceUnitLabel,
  };
}

// Fetch trend data
export async function fetchTrends(params = {}) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => { if (v != null) searchParams.set(k, v); });
  const res = await fetch(`${API_BASE}/analytics/trends?${searchParams}`);
  return res.json();
}

// Fetch scatter data
export async function fetchScatter(params = {}) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => { if (v != null) searchParams.set(k, v); });
  const res = await fetch(`${API_BASE}/analytics/scatter?${searchParams}`);
  return res.json();
}

// Fetch market comparison
export async function fetchCompare(params = {}) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => { if (v != null) searchParams.set(k, v); });
  const res = await fetch(`${API_BASE}/analytics/compare?${searchParams}`);
  return res.json();
}

// Profitability calculator
export async function calculateProfitability(body, params = {}) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => { if (v != null) searchParams.set(k, v); });
  const res = await fetch(`${API_BASE}/tools/profitability?${searchParams}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return res.json();
}
