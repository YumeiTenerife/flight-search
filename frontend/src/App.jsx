import React, { useState } from 'react';
import SearchForm from './components/SearchForm';
import FlightCard from './components/FlightCard';
import NearbyDatesChart from './components/NearbyDatesChart';
import SetAlertModal from './components/SetAlertModal';
import { api } from './api.js';
import './App.css';

const PRICE_LEVEL_CONFIG = {
  low:     { label: 'Low price',     color: '#4caf84', bg: 'rgba(76,175,132,0.12)',  icon: '↓' },
  typical: { label: 'Typical price', color: '#c9a84c', bg: 'rgba(201,168,76,0.12)', icon: '→' },
  high:    { label: 'High price',    color: '#e05a5a', bg: 'rgba(224,90,90,0.12)',   icon: '↑' },
};

function PriceInsightsBadge({ insights, currency }) {
  const cfg = PRICE_LEVEL_CONFIG[insights.price_level] || PRICE_LEVEL_CONFIG.typical;
  const symbols = { USD: '$', CAD: 'CA$', EUR: '€', GBP: '£', AUD: 'A$' };
  const sym = symbols[currency] || currency + ' ';
  const fmt = (p) => p ? `${sym}${p.toLocaleString()}` : null;
  const range = insights.typical_price_low && insights.typical_price_high
    ? `Typical: ${fmt(insights.typical_price_low)} – ${fmt(insights.typical_price_high)}`
    : null;
  return (
    <div className="price-insights-badge" style={{ '--pi-color': cfg.color, '--pi-bg': cfg.bg }}>
      <span className="pi-icon">{cfg.icon}</span>
      <div className="pi-text">
        <span className="pi-level">{cfg.label}</span>
        {range && <span className="pi-range">{range}</span>}
      </div>
    </div>
  );
}

const CURRENCIES = ['USD', 'CAD', 'EUR', 'GBP', 'AUD', 'JPY', 'CHF', 'NZD'];

const COUNTRY_TO_CURRENCY = {
  US: 'USD',
  CA: 'CAD',
  GB: 'GBP',
  AU: 'AUD',
  NZ: 'NZD',
  JP: 'JPY',
  CH: 'CHF',
  EU: 'EUR',
};

function detectCurrencyFromLocale() {
  const langs = navigator.languages || [navigator.language || 'en-US'];
  for (const lang of langs) {
    const regionMatch = lang.match(/-([A-Z]{2})$/i);
    if (!regionMatch) continue;
    const region = regionMatch[1].toUpperCase();
    if (COUNTRY_TO_CURRENCY[region]) return COUNTRY_TO_CURRENCY[region];
  }
  return 'USD';
}

async function detectCurrencyFromIp() {
  try {
    const res = await fetch('https://ipapi.co/json');
    if (!res.ok) return null;
    const json = await res.json();
    const country = (json.country || json.country_code || '').toUpperCase();
    return COUNTRY_TO_CURRENCY[country] || null;
  } catch {
    return null;
  }
}

export default function App() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastSearch, setLastSearch] = useState(null);

  const [currency, setCurrency] = useState(() => {
    if (typeof window === 'undefined') return 'USD';

    const stored = window.localStorage.getItem('currency');
    if (stored && CURRENCIES.includes(stored)) return stored;

    return detectCurrencyFromLocale();
  });

  const [showAlertModal, setShowAlertModal] = useState(false);
  const [alertSuccess, setAlertSuccess] = useState(null);

  React.useEffect(() => {
    if (typeof window === 'undefined') return;
    const explicit = window.localStorage.getItem('currencyExplicit') === 'true';
    if (explicit) return; // user explicitly chose currency

    detectCurrencyFromIp().then((ipCurrency) => {
      if (!ipCurrency) return;
      if (ipCurrency !== currency) {
        setCurrency(ipCurrency);
        window.localStorage.setItem('currency', ipCurrency);
      }
    });
  }, []);

  const handleSearch = async (params) => {
    setLoading(true);
    setError(null);
    setResults(null);
    // Always use the global currency from the header
    const mergedParams = { ...params, currency };
    setLastSearch(mergedParams);

    try {
      const query = new URLSearchParams();
      Object.entries(mergedParams).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') query.append(k, v);
      });

      const res = await api.get(`/search?${query.toString()}`);
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || `Error ${res.status}`);
      }

      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCurrencyChange = (newCurrency) => {
    setCurrency(newCurrency);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('currency', newCurrency);
      window.localStorage.setItem('currencyExplicit', 'true');
    }

    // Auto-refresh if we already have search results
    if (lastSearch) {
      handleSearch({ ...lastSearch, currency: newCurrency });
    }
  };

  return (
    <div className="app">
      {/* Background decoration */}
      <div className="bg-grid" />
      <div className="bg-glow" />

      {/* Header */}
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">✈</span>
            <span className="logo-text">Skyline</span>
          </div>
          <div className="header-controls">
            <select
              className="header-currency"
              value={currency}
              onChange={e => handleCurrencyChange(e.target.value)}
            >
              {CURRENCIES.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="hero">
        <h1 className="hero-title">
          Find your next<br />
          <em>destination</em>
        </h1>
        <p className="hero-sub">Search hundreds of airlines in seconds</p>
      </section>

      {/* Main content */}
      <main className="main">
        <div className="container">
          <SearchForm onSearch={handleSearch} loading={loading} currency={currency} />

          {/* Error */}
          {error && (
            <div className="error-box">
              <span className="error-icon">⚠</span>
              <span>{error}</span>
            </div>
          )}

          {/* Results header */}
          {results && (
            <div className="results-header">
              <div className="results-summary">
                <span className="results-count">{results.results_count}</span>
                <span className="results-label">
                  {results.results_count === 1 ? 'flight' : 'flights'} found
                </span>
                <span className="results-route">
                  {results.origin} → {results.destination}
                </span>
                <span className="results-date">{results.departure_date}</span>
              </div>
              <div className="results-actions">
                {results.price_insights && (
                  <PriceInsightsBadge insights={results.price_insights} currency={results.currency} />
                )}
                <button
                  className="set-alert-btn"
                  onClick={() => { setAlertSuccess(null); setShowAlertModal(true); }}
                >
                  🔔 Set alert
                </button>
              </div>
            </div>
          )}

          {/* Alert success message */}
          {alertSuccess && (
            <div className="alert-success-box">
              ✓ Alert created! You'll receive daily emails at <strong>{alertSuccess.email || 'your email'}</strong> when new flights are found.
            </div>
          )}

          {/* No results */}
          {results && results.results_count === 0 && (
            <div className="empty-state">
              <div className="empty-icon">✈</div>
              <div className="empty-title">No flights found</div>
              <div className="empty-sub">Try adjusting your filters or dates</div>
            </div>
          )}

          {/* Flight list */}
          {results && results.offers.length > 0 && (
            <div className="results-list">
              {results.offers.map((offer, i) => (
                <FlightCard
                  key={offer.id}
                  offer={offer}
                  currency={results.currency}
                  index={i}
                />
              ))}
            </div>
          )}

          {/* Nearby dates chart */}
          {results && lastSearch && (
            <NearbyDatesChart
              origin={results.origin}
              destination={results.destination}
              departureDate={results.departure_date}
              currency={results.currency}
              adults={lastSearch.adults || 1}
              onSelectDate={(date) => {
                const updated = { ...lastSearch, departure_date: date };
                setLastSearch(updated);
                handleSearch(updated);
              }}
            />
          )}

          {/* Loading skeleton */}
          {loading && (
            <div className="results-list">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="skeleton-card" style={{ '--delay': `${i * 80}ms` }} />
              ))}
            </div>
          )}
        </div>
      </main>

      {showAlertModal && lastSearch && (
        <SetAlertModal
          searchParams={lastSearch}
          onClose={() => setShowAlertModal(false)}
          onSuccess={(data) => {
            setShowAlertModal(false);
            setAlertSuccess({ ...data });
          }}
        />
      )}
    </div>
  );
}
