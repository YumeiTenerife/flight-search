import React, { useState } from 'react';
import './FlightCard.css';

function formatTime(isoStr) {
  if (!isoStr) return '—';
  try {
    const d = new Date(isoStr);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
  } catch {
    // Sometimes API returns already-formatted strings
    return isoStr.length > 10 ? isoStr.slice(11, 16) : isoStr;
  }
}

function formatDate(isoStr) {
  if (!isoStr) return '';
  try {
    return new Date(isoStr).toLocaleDateString([], { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
}

function StopsLabel({ stops }) {
  if (stops === 0) return <span className="stops-badge stops-nonstop">Non-stop</span>;
  return <span className="stops-badge stops-connecting">{stops} stop{stops > 1 ? 's' : ''}</span>;
}

function Leg({ itinerary, label }) {
  const first = itinerary.segments[0];
  const last = itinerary.segments[itinerary.segments.length - 1];

  return (
    <div className="leg">
      {label && <div className="leg-label">{label}</div>}
      <div className="leg-row">
        <div className="leg-endpoint">
          <div className="leg-time">{formatTime(first?.departure_time)}</div>
          <div className="leg-airport">{first?.departure_airport}</div>
          <div className="leg-date">{formatDate(first?.departure_time)}</div>
        </div>

        <div className="leg-middle">
          <div className="leg-duration">{itinerary.total_duration}</div>
          <div className="leg-line">
            <div className="leg-line-dot" />
            <div className="leg-line-track" />
            <div className="leg-plane">✈</div>
            <div className="leg-line-track" />
            <div className="leg-line-dot" />
          </div>
          <StopsLabel stops={itinerary.stops} />
        </div>

        <div className="leg-endpoint leg-endpoint--right">
          <div className="leg-time">{formatTime(last?.arrival_time)}</div>
          <div className="leg-airport">{last?.arrival_airport}</div>
          <div className="leg-date">{formatDate(last?.arrival_time)}</div>
        </div>
      </div>

      {itinerary.stops > 0 && (
        <div className="leg-segments">
          {itinerary.segments.map((seg, i) => (
            <div key={i} className="segment-detail">
              <span className="segment-fn">{seg.flight_number}</span>
              <span className="segment-carrier">{seg.carrier}</span>
              <span className="segment-route">{seg.departure_airport} → {seg.arrival_airport}</span>
              <span className="segment-dur">{seg.duration}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function FlightCard({ offer, currency, index }) {
  const [expanded, setExpanded] = useState(false);
  const isRoundtrip = offer.itineraries.length > 1;

  const CURRENCY_SYMBOLS = { USD: '$', CAD: 'CA$', EUR: '€', GBP: '£', AUD: 'A$' };
  const sym = CURRENCY_SYMBOLS[currency] || currency + ' ';

  return (
    <div className={`flight-card ${expanded ? 'flight-card--expanded' : ''}`}
         style={{ '--delay': `${index * 60}ms` }}>
      <div className="card-main">
        {/* Itineraries */}
        <div className="card-legs">
          {offer.itineraries.map((itin, i) => (
            <Leg
              key={i}
              itinerary={itin}
              label={isRoundtrip ? (i === 0 ? 'Outbound' : 'Return') : null}
            />
          ))}
        </div>

        {/* Price + actions */}
        <div className="card-aside">
          <div className="card-price">
            <span className="price-sym">{sym}</span>
            <span className="price-val">{offer.price.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</span>
          </div>
          <div className="card-meta">
            {offer.cabin_class.replace('_', ' ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase())}
          </div>
          {offer.seats_available && (
            <div className="card-seats">{offer.seats_available} seats left</div>
          )}
          <div className="card-actions">
            <button
              className="details-btn"
              onClick={() => setExpanded(e => !e)}
            >
              {expanded ? 'Hide details' : 'View details'}
            </button>
            {offer.booking_url && (
              <a
                href={offer.booking_url}
                target="_blank"
                rel="noopener noreferrer"
                className="book-btn"
              >
                Book →
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Expanded segment details */}
      {expanded && (
        <div className="card-details">
          {offer.itineraries.map((itin, i) => (
            <div key={i}>
              {isRoundtrip && (
                <div className="detail-leg-label">{i === 0 ? 'Outbound Segments' : 'Return Segments'}</div>
              )}
              {itin.segments.map((seg, j) => (
                <div key={j} className="detail-segment">
                  <div className="detail-seg-header">
                    <span className="detail-fn">{seg.flight_number}</span>
                    <span className="detail-carrier">{seg.carrier}</span>
                  </div>
                  <div className="detail-seg-row">
                    <div>
                      <div className="detail-time">{formatTime(seg.departure_time)}</div>
                      <div className="detail-airport">{seg.departure_airport}</div>
                      <div className="detail-date">{formatDate(seg.departure_time)}</div>
                    </div>
                    <div className="detail-arrow">
                      <div className="detail-duration">{seg.duration}</div>
                      <div>──────✈──────</div>
                    </div>
                    <div>
                      <div className="detail-time">{formatTime(seg.arrival_time)}</div>
                      <div className="detail-airport">{seg.arrival_airport}</div>
                      <div className="detail-date">{formatDate(seg.arrival_time)}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}