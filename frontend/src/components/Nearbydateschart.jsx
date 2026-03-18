import React, { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell
} from 'recharts';
import './NearbyDatesChart.css';

const CURRENCY_SYMBOLS = { USD: '$', CAD: 'CA$', EUR: '€', GBP: '£', AUD: 'A$' };

function formatDate(dateStr) {
  const d = new Date(dateStr + 'T12:00:00');
  return d.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
}

function formatShortDate(dateStr) {
  const d = new Date(dateStr + 'T12:00:00');
  return d.toLocaleDateString([], { weekday: 'short', day: 'numeric' });
}

const CustomTooltip = ({ active, payload, currency }) => {
  if (!active || !payload?.length) return null;
  const { date, price } = payload[0].payload;
  const sym = CURRENCY_SYMBOLS[currency] || currency + ' ';
  return (
    <div className="chart-tooltip">
      <div className="tooltip-date">{formatDate(date)}</div>
      {price !== null
        ? <div className="tooltip-price">{sym}{price.toLocaleString()}</div>
        : <div className="tooltip-unavailable">No flights found</div>
      }
    </div>
  );
};

export default function NearbyDatesChart({ origin, destination, departureDate, currency, adults, onSelectDate }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchDates = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `/nearby-dates?origin=${origin}&destination=${destination}&departure_date=${departureDate}&currency=${currency}&adults=${adults}`
      );
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || 'Failed to load nearby dates');
      setData(json.dates);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const sym = CURRENCY_SYMBOLS[currency] || currency + ' ';
  const prices = data ? data.filter(d => d.price !== null).map(d => d.price) : [];
  const minPrice = prices.length ? Math.min(...prices) : 0;
  const maxPrice = prices.length ? Math.max(...prices) : 0;

  const getBarColor = (price, date) => {
    if (price === null) return 'var(--ink-muted)';
    if (date === departureDate) return 'var(--gold)';
    const range = maxPrice - minPrice || 1;
    const ratio = (price - minPrice) / range;
    if (ratio < 0.33) return '#4caf84';
    if (ratio < 0.66) return '#c9a84c';
    return '#e05a5a';
  };

  if (!data && !loading) {
    return (
      <button className="nearby-dates-btn" onClick={fetchDates}>
        <span className="nearby-icon">📅</span>
        Compare nearby dates
      </button>
    );
  }

  return (
    <div className="nearby-dates-chart">
      <div className="chart-header">
        <div className="chart-title">
          <span>Prices ±3 days around {formatDate(departureDate)}</span>
          <span className="chart-route">{origin} → {destination}</span>
        </div>
        <button className="chart-refresh" onClick={fetchDates} disabled={loading}>
          {loading ? '...' : '↺'}
        </button>
      </div>

      {error && <div className="chart-error">⚠ {error}</div>}

      {loading && (
        <div className="chart-loading">
          <div className="chart-skeleton" />
          <p>Searching 7 dates in parallel...</p>
        </div>
      )}

      {data && !loading && (
        <>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
              onClick={(e) => {
                if (e?.activePayload?.[0]?.payload?.price !== null) {
                  onSelectDate(e.activePayload[0].payload.date);
                }
              }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
              <XAxis
                dataKey="date"
                tickFormatter={formatShortDate}
                tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tickFormatter={(v) => `${sym}${v >= 1000 ? (v/1000).toFixed(1)+'k' : v}`}
                tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={56}
              />
              <Tooltip content={<CustomTooltip currency={currency} />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
              <Bar dataKey="price" radius={[4,4,0,0]} maxBarSize={48} style={{ cursor: 'pointer' }}>
                {data.map((entry) => (
                  <Cell
                    key={entry.date}
                    fill={getBarColor(entry.price, entry.date)}
                    opacity={entry.date === departureDate ? 1 : 0.75}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          <div className="chart-legend">
            <span className="legend-item"><span className="legend-dot" style={{background:'#4caf84'}} /> Cheapest</span>
            <span className="legend-item"><span className="legend-dot" style={{background:'var(--gold)'}} /> Selected date</span>
            <span className="legend-item"><span className="legend-dot" style={{background:'#e05a5a'}} /> Most expensive</span>
            <span className="legend-item chart-hint">Click a bar to search that date</span>
          </div>
        </>
      )}
    </div>
  );
}