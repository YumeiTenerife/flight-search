import React, { useState } from 'react';
import './SetAlertModal.css';
import { api } from '../api.js';

export default function SetAlertModal({ searchParams, onClose, onSuccess }) {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.post('/alerts', {
        email,
        origin: searchParams.origin,
        destination: searchParams.destination,
        filters: searchParams,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to create alert');
      onSuccess(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <span className="modal-icon">🔔</span>
            Set flight alert
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-route">
          {searchParams.origin} → {searchParams.destination}
          <span className="modal-date">{searchParams.departure_date}</span>
        </div>

        <p className="modal-desc">
          We'll email you once a day when new flights matching your current filters are found.
        </p>

        <form className="modal-form" onSubmit={handleSubmit}>
          <div className="modal-input-wrap">
            <input
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              autoFocus
            />
          </div>
          {error && <div className="modal-error">⚠ {error}</div>}
          <button type="submit" className="modal-submit" disabled={loading}>
            {loading ? 'Creating alert...' : 'Create alert'}
          </button>
        </form>
      </div>
    </div>
  );
}
