import React, { useState } from 'react';
import './SearchForm.css';
import AirportInput from './AirportInput';

const CURRENCIES = ['USD', 'CAD', 'EUR', 'GBP', 'AUD', 'JPY', 'CHF', 'NZD'];

export default function SearchForm({ onSearch, loading }) {
  const [form, setForm] = useState({
    origin: '',
    destination: '',
    departure_date: '',
    return_date: '',
    adults: 1,
    max_price: '',
    max_stops: '',
    currency: 'USD',
    sort_by: 'price',
    trip_type: 'oneway',
    no_overnight_layover: false,
    avoid_countries: '',
    carry_on_bags: 0,
    checked_bags: 0,
  });

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }));

  const handleSubmit = (e) => {
    e.preventDefault();
    const params = { ...form };
    if (!params.return_date || params.trip_type === 'oneway') delete params.return_date;
    if (!params.max_price) delete params.max_price;
    if (params.max_stops === '') delete params.max_stops;
    if (!params.avoid_countries) delete params.avoid_countries;
    delete params.trip_type;
    onSearch(params);
  };

  const today = new Date().toISOString().split('T')[0];

  return (
    <form className="search-form" onSubmit={handleSubmit}>

      {/* Top row: trip toggle + currency */}
      <div className="form-top-row">
        <div className="trip-toggle">
          {['oneway', 'roundtrip'].map(t => (
            <button
              key={t}
              type="button"
              className={`toggle-btn ${form.trip_type === t ? 'active' : ''}`}
              onClick={() => set('trip_type', t)}
            >
              {t === 'oneway' ? 'One Way' : 'Round Trip'}
            </button>
          ))}
        </div>

        <div className="currency-select">
          <select value={form.currency} onChange={e => set('currency', e.target.value)}>
            {CURRENCIES.map(c => <option key={c}>{c}</option>)}
          </select>
        </div>
      </div>

      <div className="form-grid">
        <AirportInput
          label="From"
          icon="✈"
          placeholder="City or airport..."
          value={form.origin}
          onChange={val => set('origin', val)}
          required
        />

        <AirportInput
          label="To"
          icon="🏁"
          placeholder="City or airport..."
          value={form.destination}
          onChange={val => set('destination', val)}
          required
        />

        <div className="form-group">
          <label>Departure</label>
          <div className="input-wrap">
            <input
              type="date"
              min={today}
              value={form.departure_date}
              onChange={e => set('departure_date', e.target.value)}
              required
            />
          </div>
        </div>

        {form.trip_type === 'roundtrip' && (
          <div className="form-group">
            <label>Return</label>
            <div className="input-wrap">
              <input
                type="date"
                min={form.departure_date || today}
                value={form.return_date}
                onChange={e => set('return_date', e.target.value)}
                required
              />
            </div>
          </div>
        )}

        <div className="form-group form-group--sm">
          <label>Adults</label>
          <div className="input-wrap">
            <input
              type="number"
              min={1} max={9}
              value={form.adults}
              onChange={e => set('adults', parseInt(e.target.value))}
            />
          </div>
        </div>

        <div className="form-group form-group--sm">
          <label>Max Stops</label>
          <div className="input-wrap">
            <select value={form.max_stops} onChange={e => set('max_stops', e.target.value)}>
              <option value="">Any</option>
              <option value="0">Non-stop</option>
              <option value="1">1 stop</option>
              <option value="2">2 stops</option>
            </select>
          </div>
        </div>

        <div className="form-group form-group--sm">
          <label>Max Price</label>
          <div className="input-wrap">
            <input
              type="number"
              placeholder="Any"
              min={0}
              value={form.max_price}
              onChange={e => set('max_price', e.target.value)}
            />
          </div>
        </div>

        <div className="form-group form-group--sm">
          <label>Sort By</label>
          <div className="input-wrap">
            <select value={form.sort_by} onChange={e => set('sort_by', e.target.value)}>
              <option value="price">Price</option>
              <option value="stops">Stops</option>
              <option value="duration">Duration</option>
            </select>
          </div>
        </div>
      </div>

      {/* Extra filters */}
      <div className="extra-filters">
        <div className="filters-title">Filters</div>
        <div className="filters-row">

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={form.no_overnight_layover}
              onChange={e => set('no_overnight_layover', e.target.checked)}
            />
            <span className="checkbox-custom" />
            <div className="checkbox-text-wrap">
              <span className="checkbox-text">No overnight layovers</span>
              <span className="checkbox-hint">Skip connections 12+ hours spanning midnight</span>
            </div>
          </label>

          <div className="avoid-countries-wrap">
            <label className="avoid-label">Avoid connections in</label>
            <div className="input-wrap avoid-input">
              <input
                type="text"
                placeholder="e.g. US, TR, AE"
                value={form.avoid_countries}
                onChange={e => set('avoid_countries', e.target.value.toUpperCase())}
              />
            </div>
            <span className="avoid-hint">ISO country codes, comma-separated</span>
          </div>

          <div className="bags-wrap">
            <div className="bags-label">Bags</div>
            <div className="bags-row">
              <div className="bag-selector">
                <span className="bag-icon">🎒</span>
                <span className="bag-name">Carry-on</span>
                <div className="bag-counter">
                  <button type="button" className="counter-btn"
                    onClick={() => set('carry_on_bags', Math.max(0, form.carry_on_bags - 1))}>−</button>
                  <span className="counter-val">{form.carry_on_bags}</span>
                  <button type="button" className="counter-btn"
                    onClick={() => set('carry_on_bags', Math.min(form.adults, form.carry_on_bags + 1))}>+</button>
                </div>
              </div>
              <div className="bag-selector">
                <span className="bag-icon">🧳</span>
                <span className="bag-name">Checked</span>
                <div className="bag-counter">
                  <button type="button" className="counter-btn"
                    onClick={() => set('checked_bags', Math.max(0, form.checked_bags - 1))}>−</button>
                  <span className="counter-val">{form.checked_bags}</span>
                  <button type="button" className="counter-btn"
                    onClick={() => set('checked_bags', Math.min(form.adults, form.checked_bags + 1))}>+</button>
                </div>
              </div>
            </div>
            <span className="avoid-hint">Price updates to include bag fees</span>
          </div>

        </div>
      </div>

      <button type="submit" className="search-btn" disabled={loading}>
        {loading ? (
          <span className="btn-loading">
            <span className="spinner" /> Searching...
          </span>
        ) : (
          'Search Flights'
        )}
      </button>
    </form>
  );
}