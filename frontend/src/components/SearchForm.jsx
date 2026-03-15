import React, { useState } from 'react';
import './SearchForm.css';

const CABIN_CLASSES = ['Economy', 'Premium_Economy', 'Business', 'First'];
const CURRENCIES = ['USD', 'CAD', 'EUR', 'GBP', 'AUD'];

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
  });

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }));

  const handleSubmit = (e) => {
    e.preventDefault();
    const params = { ...form };
    if (!params.return_date || params.trip_type === 'oneway') delete params.return_date;
    if (!params.max_price) delete params.max_price;
    if (params.max_stops === '') delete params.max_stops;
    delete params.trip_type;
    onSearch(params);
  };

  const today = new Date().toISOString().split('T')[0];

  return (
    <form className="search-form" onSubmit={handleSubmit}>
      {/* Trip type toggle */}
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

      <div className="form-grid">
        {/* Origin */}
        <div className="form-group">
          <label>From</label>
          <div className="input-wrap">
            <span className="input-icon">✈</span>
            <input
              type="text"
              placeholder="YYZ"
              maxLength={3}
              value={form.origin}
              onChange={e => set('origin', e.target.value.toUpperCase())}
              required
            />
          </div>
        </div>

        {/* Destination */}
        <div className="form-group">
          <label>To</label>
          <div className="input-wrap">
            <span className="input-icon">🏁</span>
            <input
              type="text"
              placeholder="LHR"
              maxLength={3}
              value={form.destination}
              onChange={e => set('destination', e.target.value.toUpperCase())}
              required
            />
          </div>
        </div>

        {/* Departure date */}
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

        {/* Return date */}
        {form.trip_type === 'roundtrip' && (
          <div className="form-group">
            <label>Return</label>
            <div className="input-wrap">
              <input
                type="date"
                min={form.departure_date || today}
                value={form.return_date}
                onChange={e => set('return_date', e.target.value)}
                required={form.trip_type === 'roundtrip'}
              />
            </div>
          </div>
        )}

        {/* Adults */}
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

        {/* Max stops */}
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

        {/* Currency */}
        <div className="form-group form-group--sm">
          <label>Currency</label>
          <div className="input-wrap">
            <select value={form.currency} onChange={e => set('currency', e.target.value)}>
              {CURRENCIES.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
        </div>

        {/* Max price */}
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

        {/* Sort */}
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