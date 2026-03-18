import { useState, useEffect } from 'react';
import { Save, RotateCcw } from 'lucide-react';
import { api } from '../../utils/api';
import LoadingSpinner from '../shared/LoadingSpinner';
import EditableInput from '../shared/EditableInput';

const WEIGHT_LABELS = {
  integration: 'Integration Fit',
  high_value_crop: 'High-Value Crops',
  registration_ease: 'Registration Ease',
  scale_potential: 'Scale Potential',
  strategic_leverage: 'Strategic Leverage',
  penalty_complexity: 'Complexity Penalty',
};

const THRESHOLD_LABELS = {
  tier_1_min: 'Tier 1 Minimum',
  tier_2_min: 'Tier 2 Minimum',
  tier_3_min: 'Tier 3 Minimum',
};

export default function SettingsView() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    api.getScoringConfig().then(setConfig).finally(() => setLoading(false));
  }, []);

  const updateWeight = (key, value) => {
    setConfig(prev => ({
      ...prev,
      scoring_weights: { ...prev.scoring_weights, [key]: value },
    }));
    setDirty(true);
  };

  const updateThreshold = (key, value) => {
    setConfig(prev => ({
      ...prev,
      tier_thresholds: { ...prev.tier_thresholds, [key]: value },
    }));
    setDirty(true);
  };

  const updateRevenue = (key, value) => {
    setConfig(prev => ({
      ...prev,
      revenue_assumptions: { ...prev.revenue_assumptions, [key]: value },
    }));
    setDirty(true);
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      await api.updateScoringConfig(config);
      setDirty(false);
      setMessage({ type: 'success', text: 'Settings saved successfully.' });
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to save: ' + err.message });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setLoading(true);
    api.getScoringConfig().then(c => { setConfig(c); setDirty(false); }).finally(() => setLoading(false));
  };

  if (loading) return <LoadingSpinner text="Loading settings..." />;
  if (!config) return <div className="page-body">Failed to load settings.</div>;

  const weights = config.scoring_weights;
  const positiveWeights = Object.entries(weights).filter(([k]) => k !== 'penalty_complexity');
  const weightSum = positiveWeights.reduce((s, [, v]) => s + v, 0);

  return (
    <>
      <div className="page-header">
        <div className="flex items-center justify-between" style={{ width: '100%' }}>
          <div>
            <h1>Settings</h1>
            <p style={{ color: 'var(--text-secondary)', marginTop: 4 }}>
              Scoring weights, tier thresholds, and revenue assumptions
            </p>
          </div>
          <div className="flex gap-2">
            <button className="btn" onClick={handleReset} disabled={!dirty}>
              <RotateCcw size={14} style={{ marginRight: 4 }} /> Reset
            </button>
            <button className="btn btn-primary" onClick={handleSave} disabled={!dirty || saving}>
              <Save size={14} style={{ marginRight: 4 }} /> {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </div>
      <div className="page-body">
        {message && (
          <div style={{
            padding: '10px 16px', borderRadius: 8, marginBottom: 16,
            background: message.type === 'success' ? 'rgba(76,175,80,0.15)' : 'rgba(239,83,80,0.15)',
            color: message.type === 'success' ? 'var(--success)' : 'var(--danger)',
            fontSize: '0.85rem',
          }}>
            {message.text}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          {/* Scoring Weights */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Scoring Weights</span>
              <span style={{
                fontSize: '0.75rem', marginLeft: 8,
                color: Math.abs(weightSum - 1) < 0.01 ? 'var(--success)' : 'var(--danger)',
              }}>
                (Sum: {(weightSum * 100).toFixed(0)}%)
              </span>
            </div>
            {Object.entries(WEIGHT_LABELS).map(([key, label]) => (
              <div key={key} className="flex items-center justify-between" style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{label}</span>
                <div className="flex items-center gap-2">
                  <input
                    type="range"
                    min={key === 'penalty_complexity' ? -0.5 : 0}
                    max={key === 'penalty_complexity' ? 0 : 0.5}
                    step={0.05}
                    value={weights[key]}
                    onChange={e => updateWeight(key, parseFloat(e.target.value))}
                    style={{ width: 120 }}
                  />
                  <span style={{ fontWeight: 600, width: 50, textAlign: 'right', fontSize: '0.85rem' }}>
                    {(weights[key] * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Tier Thresholds */}
          <div>
            <div className="card mb-4">
              <div className="card-header"><span className="card-title">Tier Thresholds</span></div>
              {Object.entries(THRESHOLD_LABELS).map(([key, label]) => (
                <div key={key} className="flex items-center justify-between" style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{label}</span>
                  <EditableInput
                    value={config.tier_thresholds[key]}
                    onChange={v => updateThreshold(key, v)}
                    min={0}
                    max={5}
                    step={0.1}
                  />
                </div>
              ))}
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 8 }}>
                Companies scoring below Tier 3 minimum are assigned Tier 4.
              </p>
            </div>

            {/* Revenue Assumptions */}
            <div className="card">
              <div className="card-header"><span className="card-title">Revenue Assumptions</span></div>
              <div className="flex items-center justify-between" style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Coverage %</span>
                <EditableInput
                  value={config.revenue_assumptions.coverage_pct * 100}
                  onChange={v => updateRevenue('coverage_pct', v / 100)}
                  min={0} max={100} step={5} suffix="%"
                />
              </div>
              <div className="flex items-center justify-between" style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Application Rate (L/ha)</span>
                <EditableInput
                  value={config.revenue_assumptions.application_rate_litres_per_ha}
                  onChange={v => updateRevenue('application_rate_litres_per_ha', v)}
                  min={0.1} max={20} step={0.5}
                />
              </div>
              <div className="flex items-center justify-between" style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Applications/Season</span>
                <EditableInput
                  value={config.revenue_assumptions.applications_per_season}
                  onChange={v => updateRevenue('applications_per_season', Math.round(v))}
                  min={1} max={10} step={1}
                />
              </div>
              <div className="flex items-center justify-between" style={{ padding: '8px 0' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Price/Litre (EUR)</span>
                <EditableInput
                  value={config.revenue_assumptions.price_per_litre_eur}
                  onChange={v => updateRevenue('price_per_litre_eur', v)}
                  min={0.5} max={50} step={0.5} prefix="€"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
