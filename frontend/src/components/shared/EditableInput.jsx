import { useState, useRef, useEffect } from 'react';

export default function EditableInput({ value, onChange, min, max, step = 1, suffix = '', prefix = '', className = '' }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const inputRef = useRef();

  useEffect(() => { setDraft(value); }, [value]);
  useEffect(() => { if (editing && inputRef.current) inputRef.current.select(); }, [editing]);

  const commit = () => {
    setEditing(false);
    const v = parseFloat(draft);
    if (!isNaN(v)) onChange(Math.min(max ?? Infinity, Math.max(min ?? -Infinity, v)));
  };

  if (editing) {
    return (
      <input
        ref={inputRef}
        type="number"
        value={draft}
        min={min}
        max={max}
        step={step}
        onChange={e => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={e => { if (e.key === 'Enter') commit(); if (e.key === 'Escape') setEditing(false); }}
        className={`w-20 text-right ${className}`}
        style={{ padding: '2px 6px', fontSize: '0.875rem' }}
      />
    );
  }

  return (
    <span
      onClick={() => setEditing(true)}
      className={`cursor-pointer hover:underline ${className}`}
      style={{ color: 'var(--interactive)', fontWeight: 500 }}
      title="Click to edit"
    >
      {prefix}{typeof value === 'number' ? value.toLocaleString('en', { maximumFractionDigits: 2 }) : value}{suffix}
    </span>
  );
}
