import { useState } from 'react';
import { Edit3, Save, X } from 'lucide-react';
import ScoreBar from './ScoreBar';
import TierBadge from '../shared/TierBadge';

const SCORE_KEYS = [
  'integration', 'high_value_crop', 'registration_ease',
  'scale_potential', 'strategic_leverage', 'penalty_complexity',
];

export default function ScorePanel({ company, weights, onSave }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState({ ...company.scores });

  const handleUpdate = (name, value) => {
    setDraft(prev => ({ ...prev, [name]: value }));
  };

  const handleSave = () => {
    onSave(draft);
    setEditing(false);
  };

  const handleCancel = () => {
    setDraft({ ...company.scores });
    setEditing(false);
  };

  const scores = editing ? draft : company.scores;

  return (
    <div className="card">
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="card-title">Scoring Matrix</span>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <TierBadge tier={company.tier} label={company.tier_label} />
          <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>{company.weighted_score.toFixed(2)}</span>
          {!editing ? (
            <button className="btn btn-sm" onClick={() => setEditing(true)} title="Edit scores">
              <Edit3 size={14} />
            </button>
          ) : (
            <>
              <button className="btn btn-sm btn-primary" onClick={handleSave} title="Save">
                <Save size={14} />
              </button>
              <button className="btn btn-sm" onClick={handleCancel} title="Cancel">
                <X size={14} />
              </button>
            </>
          )}
        </div>
      </div>
      <div style={{ padding: '12px 0' }}>
        {SCORE_KEYS.map(key => (
          <ScoreBar
            key={key}
            name={key}
            value={scores[key]}
            weight={weights?.[key]}
            editable={editing}
            onUpdate={handleUpdate}
          />
        ))}
      </div>
    </div>
  );
}
