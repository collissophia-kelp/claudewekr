import { useState } from 'react';

const LABELS = {
  integration: 'Integration Fit',
  high_value_crop: 'High-Value Crops',
  registration_ease: 'Registration Ease',
  scale_potential: 'Scale Potential',
  strategic_leverage: 'Strategic Leverage',
  penalty_complexity: 'Complexity Penalty',
};

export default function ScoreBar({ name, value, weight, onUpdate, editable = false }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const isPenalty = name === 'penalty_complexity';
  const max = 5;
  const pct = Math.min(100, (Math.abs(value) / max) * 100);

  const commit = (v) => {
    setEditing(false);
    const clamped = isPenalty
      ? Math.max(0, Math.min(max, parseFloat(v) || 0))
      : Math.max(0, Math.min(max, parseFloat(v) || 0));
    onUpdate?.(name, clamped);
  };

  return (
    <div className="score-bar-row" style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
      <div style={{ width: 140, fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
        {LABELS[name] || name}
        {weight != null && (
          <span style={{ color: 'var(--text-muted)', marginLeft: 4 }}>({(weight * 100).toFixed(0)}%)</span>
        )}
      </div>
      <div style={{ flex: 1, position: 'relative', height: 20, background: 'var(--surface-raised)', borderRadius: 4, overflow: 'hidden' }}>
        <div
          style={{
            width: `${pct}%`,
            height: '100%',
            background: isPenalty ? 'var(--danger)' : value >= 4 ? 'var(--success)' : value >= 3 ? 'var(--interactive)' : 'var(--warning)',
            borderRadius: 4,
            transition: 'width 0.3s ease',
          }}
        />
      </div>
      <div style={{ width: 50, textAlign: 'right' }}>
        {editable && editing ? (
          <input
            type="number"
            min={0}
            max={max}
            step={0.5}
            value={draft}
            onChange={e => setDraft(e.target.value)}
            onBlur={() => commit(draft)}
            onKeyDown={e => { if (e.key === 'Enter') commit(draft); if (e.key === 'Escape') setEditing(false); }}
            autoFocus
            style={{ width: 50, padding: '2px 4px', textAlign: 'right', fontSize: '0.85rem' }}
          />
        ) : (
          <span
            onClick={() => { if (editable) { setDraft(value); setEditing(true); } }}
            style={{
              fontWeight: 600,
              cursor: editable ? 'pointer' : 'default',
              color: editable ? 'var(--interactive)' : 'var(--text-primary)',
            }}
            title={editable ? 'Click to edit' : undefined}
          >
            {value.toFixed(1)}
          </span>
        )}
      </div>
    </div>
  );
}
