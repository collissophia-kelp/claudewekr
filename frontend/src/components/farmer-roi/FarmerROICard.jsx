import { useState, useEffect } from 'react';
import { api } from '../../utils/api';
import { fmtCurrency, fmtNumber, fmtPct } from '../../utils/formatters';
import EditableInput from '../shared/EditableInput';
import UpliftTable from './UpliftTable';
import ROIChart from './ROIChart';
import LoadingSpinner from '../shared/LoadingSpinner';

export default function FarmerROICard({ defaultCrop = '', defaultCountry = '' }) {
  const [crop, setCrop] = useState(defaultCrop);
  const [country, setCountry] = useState(defaultCountry);
  const [areaHa, setAreaHa] = useState(100);
  const [roi, setRoi] = useState(null);
  const [loading, setLoading] = useState(false);
  const [baselines, setBaselines] = useState([]);

  useEffect(() => {
    api.getCropBaselines().then(setBaselines).catch(() => {});
  }, []);

  useEffect(() => {
    if (!crop || !country) return;
    setLoading(true);
    api.getFarmerROI(crop, country, areaHa)
      .then(setRoi)
      .catch(() => setRoi(null))
      .finally(() => setLoading(false));
  }, [crop, country, areaHa]);

  const crops = [...new Set(baselines.map(b => b.crop))].sort();
  const countries = [...new Set(baselines.filter(b => !crop || b.crop === crop).map(b => b.country))].sort();

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Farmer ROI Model</span>
      </div>

      <div className="flex gap-3 mb-4 flex-wrap items-center">
        <select value={crop} onChange={e => setCrop(e.target.value)}>
          <option value="">Select Crop</option>
          {crops.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <select value={country} onChange={e => setCountry(e.target.value)}>
          <option value="">Select Country</option>
          {countries.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <div className="flex items-center gap-2" style={{ fontSize: '0.85rem' }}>
          <span style={{ color: 'var(--text-muted)' }}>Area (ha):</span>
          <EditableInput value={areaHa} onChange={setAreaHa} min={1} max={100000} step={10} />
        </div>
      </div>

      {loading && <LoadingSpinner text="Calculating ROI..." />}

      {roi && !loading && (
        <>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Break-Even Uplift</div>
              <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--warning)' }}>
                {fmtPct(roi.break_even_uplift_pct)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Best Scenario ROI</div>
              <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--success)' }}>
                {roi.scenarios.length > 0 ? fmtPct(roi.scenarios[roi.scenarios.length - 1].roi_pct) : '—'}
              </div>
            </div>
          </div>

          <ROIChart scenarios={roi.scenarios} />
          <div style={{ marginTop: 16 }}>
            <UpliftTable scenarios={roi.scenarios} />
          </div>
        </>
      )}

      {!crop && !loading && (
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: 24 }}>
          Select a crop and country to see ROI analysis
        </p>
      )}
    </div>
  );
}
