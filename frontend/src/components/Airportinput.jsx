import React, { useState, useEffect, useRef } from 'react';
import './AirportInput.css';

export default function AirportInput({ label, icon, value, onChange, placeholder, required }) {
  const [query, setQuery] = useState(value || '');
  const [suggestions, setSuggestions] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(null);
  const debounceRef = useRef(null);
  const wrapRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const fetchSuggestions = (q) => {
    if (q.length < 2) { setSuggestions([]); setOpen(false); return; }
    setLoading(true);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await fetch(`/autocomplete?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        setSuggestions(data.suggestions || []);
        setOpen(true);
      } catch {
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 320);
  };

  const handleInput = (e) => {
    const val = e.target.value;
    setQuery(val);
    setSelected(null);
    onChange(''); // clear IATA until user picks
    fetchSuggestions(val);
  };

  const handleSelect = (s) => {
    setQuery(`${s.city} (${s.id})`);
    setSelected(s);
    onChange(s.id);
    setOpen(false);
    setSuggestions([]);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') setOpen(false);
  };

  return (
    <div className="airport-group" ref={wrapRef}>
      <label className="airport-label">{label}</label>
      <div className={`airport-input-wrap ${open && suggestions.length ? 'airport-open' : ''}`}>
        <span className="airport-icon">{icon}</span>
        <input
          type="text"
          className="airport-input"
          placeholder={placeholder}
          value={query}
          onChange={handleInput}
          onFocus={() => suggestions.length && setOpen(true)}
          onKeyDown={handleKeyDown}
          required={required && !selected}
          autoComplete="off"
          spellCheck="false"
        />
        {loading && <span className="airport-spinner" />}
        {selected && <span className="airport-check">✓</span>}
      </div>

      {open && suggestions.length > 0 && (
        <ul className="airport-dropdown">
          {suggestions.map((s, i) => (
            <li key={i} className="airport-option" onMouseDown={() => handleSelect(s)}>
              <span className="option-code">{s.id}</span>
              <div className="option-info">
                <span className="option-name">{s.name}</span>
                <span className="option-city">{s.city}{s.distance ? ` · ${s.distance}` : ''}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}