import React, { useState } from 'react';
import SearchForm from './components/SearchForm.jsx';
import FlightCard from './components/FlightCard.jsx';
import './App.css';

export default function App() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastSearch, setLastSearch] = useState(null);

  const handleSearch = async (params) => {
    setLoading(true);
    setError(null);
    setResults(null);
    setLastSearch(params);

    try {
      const query = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') query.append(k, v);
      });

      const res = await fetch(`/search?${query.toString()}`);
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
          <div className="header-tagline">Flight Search</div>
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
          <SearchForm onSearch={handleSearch} loading={loading} />

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
    </div>
  );
}