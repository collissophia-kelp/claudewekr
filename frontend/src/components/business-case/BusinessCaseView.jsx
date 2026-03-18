import { useState, useEffect } from 'react';
import { api } from '../../utils/api';
import { fmtCurrency, fmtNumber } from '../../utils/formatters';
import ProjectionTable from './ProjectionTable';
import ProjectionChart from './ProjectionChart';
import EditableInput from '../shared/EditableInput';
import LoadingSpinner from '../shared/LoadingSpinner';

export default function BusinessCaseView({ companyName, hectares }) {
  const [projections, setProjections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [rampYears, setRampYears] = useState(3);
  const [customHa, setCustomHa] = useState(hectares || 10000);

  useEffect(() => {
    setLoading(true);
    api.getProjections(companyName, customHa, rampYears)
      .then(setProjections)
      .catch(() => setProjections([]))
      .finally(() => setLoading(false));
  }, [companyName, customHa, rampYears]);

  const totalRevenue = projections.reduce((sum, p) => sum + p.revenue_eur, 0);
  const totalLitres = projections.reduce((sum, p) => sum + p.litres_required, 0);
  const peakRevenue = Math.max(0, ...projections.map(p => p.revenue_eur));

  return (
    <div className="card">
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="card-title">10-Year Business Case</span>
        <div className="flex items-center gap-4" style={{ fontSize: '0.8rem' }}>
          <div className="flex items-center gap-2">
            <span style={{ color: 'var(--text-muted)' }}>Hectares:</span>
            <EditableInput value={customHa} onChange={setCustomHa} min={100} max={10000000} step={1000} />
          </div>
          <div className="flex items-center gap-2">
            <span style={{ color: 'var(--text-muted)' }}>Ramp Years:</span>
            <EditableInput value={rampYears} onChange={v => setRampYears(Math.round(v))} min={1} max={10} step={1} />
          </div>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner text="Calculating projections..." />
      ) : (
        <>
          {/* Summary stats */}
          <div className="grid grid-cols-3 gap-4 mb-4" style={{ padding: '12px 0' }}>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>10-Year Revenue</div>
              <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--success)' }}>{fmtCurrency(totalRevenue)}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Total Volume</div>
              <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>{fmtNumber(totalLitres)} L</div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Peak Annual Revenue</div>
              <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--interactive)' }}>{fmtCurrency(peakRevenue)}</div>
            </div>
          </div>

          <ProjectionChart projections={projections} />
          <div style={{ marginTop: 16 }}>
            <ProjectionTable projections={projections} />
          </div>
        </>
      )}
    </div>
  );
}
