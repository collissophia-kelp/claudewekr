import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, MapPin, TrendingUp, BarChart3 } from 'lucide-react';
import { api } from '../../utils/api';
import { fmtCurrency, fmtNumber } from '../../utils/formatters';
import TierBadge from '../shared/TierBadge';
import StageBadge from '../shared/StageBadge';
import LoadingSpinner from '../shared/LoadingSpinner';
import PipelineFunnel from './PipelineFunnel';
import TierDistribution from './TierDistribution';

export default function DashboardView() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.getDashboardSummary().then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner text="Loading dashboard..." />;
  if (!data) return <div className="page-body">Failed to load dashboard</div>;

  const stats = [
    { icon: Building2, label: 'Active Companies', value: data.total_active, color: 'var(--interactive)' },
    { icon: MapPin, label: 'Total Hectares', value: fmtNumber(data.total_hectares), color: 'var(--stimblue-green)' },
    { icon: TrendingUp, label: 'Projected Revenue', value: fmtCurrency(data.total_projected_revenue), color: 'var(--success)' },
    { icon: BarChart3, label: 'Excluded', value: data.total_excluded, color: 'var(--text-muted)' },
  ];

  return (
    <>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: 4 }}>Stimblue+ Strategic Partnership Overview</p>
      </div>
      <div className="page-body">
        {/* Stat cards */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {stats.map(({ icon: Icon, label, value, color }) => (
            <div className="card" key={label}>
              <div className="flex items-center gap-3">
                <div style={{ background: `${color}20`, borderRadius: 8, padding: 8 }}>
                  <Icon size={20} style={{ color }} />
                </div>
                <div>
                  <div className="stat-value">{value}</div>
                  <div className="stat-label">{label}</div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Pipeline + Tiers */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="card">
            <div className="card-header"><span className="card-title">Pipeline Funnel</span></div>
            <PipelineFunnel funnel={data.pipeline_funnel} />
          </div>
          <div className="card">
            <div className="card-header"><span className="card-title">Tier Distribution</span></div>
            <TierDistribution tiers={data.tier_distribution} />
          </div>
        </div>

        {/* Top companies */}
        <div className="card">
          <div className="card-header"><span className="card-title">Top Companies by Score</span></div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Company</th>
                <th>HQ</th>
                <th>Region</th>
                <th>Score</th>
                <th>Tier</th>
                <th>Stage</th>
                <th className="text-right">Hectares</th>
                <th className="text-right">Revenue</th>
              </tr>
            </thead>
            <tbody>
              {data.top_companies.map(c => (
                <tr key={c.company_name} onClick={() => navigate(`/analyse/${encodeURIComponent(c.company_name)}`)}>
                  <td style={{ fontWeight: 600 }}>{c.company_name}</td>
                  <td style={{ color: 'var(--text-secondary)' }}>{c.hq_country}</td>
                  <td style={{ color: 'var(--text-secondary)' }}>{c.region}</td>
                  <td>{c.weighted_score.toFixed(2)}</td>
                  <td><TierBadge tier={c.tier} label={c.tier_label} /></td>
                  <td><StageBadge stage={c.pipeline_stage} /></td>
                  <td className="text-right">{fmtNumber(c.hectares_controlled)}</td>
                  <td className="text-right">{fmtCurrency(c.projected_revenue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
