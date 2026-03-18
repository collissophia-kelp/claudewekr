import { MapPin, Wheat, Globe, Building2 } from 'lucide-react';
import { fmtNumber, fmtCurrency } from '../../utils/formatters';

export default function CompanyOverview({ company }) {
  return (
    <div className="card">
      <div className="card-header"><span className="card-title">Company Overview</span></div>
      <div className="grid grid-cols-2 gap-4" style={{ padding: '12px 0' }}>
        <div className="flex items-center gap-2">
          <Building2 size={16} style={{ color: 'var(--text-muted)' }} />
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Business Type</div>
            <div style={{ fontWeight: 500 }}>{company.business_type || '—'}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <MapPin size={16} style={{ color: 'var(--text-muted)' }} />
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>HQ Country</div>
            <div style={{ fontWeight: 500 }}>{company.hq_country}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Globe size={16} style={{ color: 'var(--text-muted)' }} />
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Region</div>
            <div style={{ fontWeight: 500 }}>{company.region}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Wheat size={16} style={{ color: 'var(--text-muted)' }} />
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Farm Countries</div>
            <div style={{ fontWeight: 500 }}>{company.countries_with_controlled_farms || '—'}</div>
          </div>
        </div>
      </div>

      <div style={{ borderTop: '1px solid var(--border)', paddingTop: 12, marginTop: 4 }}>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 8 }}>Key Crops</div>
        <div className="flex gap-2 flex-wrap">
          {company.main_crops.map(crop => (
            <span key={crop} style={{
              background: 'var(--surface-raised)', padding: '4px 10px', borderRadius: 12,
              fontSize: '0.8rem', color: 'var(--text-secondary)',
            }}>
              {crop}
            </span>
          ))}
          {company.main_crops.length === 0 && <span style={{ color: 'var(--text-muted)' }}>No crops listed</span>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4" style={{ borderTop: '1px solid var(--border)', paddingTop: 12, marginTop: 12 }}>
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Hectares Controlled</div>
          <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>
            {company.hectares_controlled ? fmtNumber(company.hectares_controlled) : '—'}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Projected Revenue</div>
          <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--success)' }}>
            {company.projected_revenue ? fmtCurrency(company.projected_revenue) : '—'}
          </div>
        </div>
      </div>

      {company.notes && (
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 12, marginTop: 12 }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 4 }}>Notes</div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{company.notes}</div>
        </div>
      )}
    </div>
  );
}
