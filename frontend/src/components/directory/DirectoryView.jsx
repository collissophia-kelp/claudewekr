import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, ChevronDown, ChevronRight } from 'lucide-react';
import { api } from '../../utils/api';
import { fmtNumber, fmtCurrency } from '../../utils/formatters';
import TierBadge from '../shared/TierBadge';
import StageBadge from '../shared/StageBadge';
import LoadingSpinner from '../shared/LoadingSpinner';

export default function DirectoryView() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterRegion, setFilterRegion] = useState('');
  const [filterTier, setFilterTier] = useState('');
  const [filterStage, setFilterStage] = useState('');
  const [collapsed, setCollapsed] = useState({});
  const [sortCol, setSortCol] = useState('weighted_score');
  const [sortDir, setSortDir] = useState('desc');
  const navigate = useNavigate();

  useEffect(() => {
    api.getCompanies({ include_excluded: false }).then(setCompanies).finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    let list = companies;
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(c =>
        c.company_name.toLowerCase().includes(q) ||
        c.hq_country.toLowerCase().includes(q) ||
        c.main_crops.some(cr => cr.toLowerCase().includes(q))
      );
    }
    if (filterRegion) list = list.filter(c => c.region === filterRegion);
    if (filterTier) list = list.filter(c => c.tier === parseInt(filterTier));
    if (filterStage) list = list.filter(c => c.pipeline_stage === filterStage);

    list = [...list].sort((a, b) => {
      const va = a[sortCol], vb = b[sortCol];
      const cmp = typeof va === 'string' ? va.localeCompare(vb) : (va - vb);
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return list;
  }, [companies, search, filterRegion, filterTier, filterStage, sortCol, sortDir]);

  const regions = useMemo(() => [...new Set(companies.map(c => c.region).filter(Boolean))].sort(), [companies]);
  const grouped = useMemo(() => {
    const g = {};
    filtered.forEach(c => {
      const r = c.region || 'Unknown';
      (g[r] = g[r] || []).push(c);
    });
    return g;
  }, [filtered]);

  const toggleSort = (col) => {
    if (sortCol === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortCol(col); setSortDir('desc'); }
  };

  const toggleRegion = (r) => setCollapsed(prev => ({ ...prev, [r]: !prev[r] }));

  if (loading) return <LoadingSpinner text="Loading directory..." />;

  const tierCounts = { 1: 0, 2: 0, 3: 0, 4: 0 };
  filtered.forEach(c => tierCounts[c.tier]++);

  return (
    <>
      <div className="page-header">
        <h1>Global Company Directory</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: 4 }}>
          {filtered.length} companies | T1: {tierCounts[1]} | T2: {tierCounts[2]} | T3: {tierCounts[3]} | T4: {tierCounts[4]}
        </p>
      </div>
      <div className="page-body">
        {/* Filters */}
        <div className="flex gap-3 mb-4 flex-wrap items-center">
          <div className="relative flex-1 min-w-[200px]">
            <Search size={16} style={{ position: 'absolute', left: 10, top: 10, color: 'var(--text-muted)' }} />
            <input
              type="search" placeholder="Search companies, crops, countries..."
              value={search} onChange={e => setSearch(e.target.value)}
              style={{ paddingLeft: 32, width: '100%' }}
            />
          </div>
          <select value={filterRegion} onChange={e => setFilterRegion(e.target.value)}>
            <option value="">All Regions</option>
            {regions.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
          <select value={filterTier} onChange={e => setFilterTier(e.target.value)}>
            <option value="">All Tiers</option>
            <option value="1">Tier 1</option>
            <option value="2">Tier 2</option>
            <option value="3">Tier 3</option>
            <option value="4">Tier 4</option>
          </select>
          <select value={filterStage} onChange={e => setFilterStage(e.target.value)}>
            <option value="">All Stages</option>
            {['L5','L4','L3','L2','L1','L0'].map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        {/* Grouped table */}
        {Object.entries(grouped).sort(([a],[b]) => a.localeCompare(b)).map(([region, cos]) => (
          <div key={region} className="mb-3">
            <div
              className="flex items-center gap-2 cursor-pointer py-2 px-3"
              style={{ background: 'var(--surface-raised)', borderRadius: 8 }}
              onClick={() => toggleRegion(region)}
            >
              {collapsed[region] ? <ChevronRight size={16} /> : <ChevronDown size={16} />}
              <span style={{ fontWeight: 600 }}>{region}</span>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>({cos.length} companies)</span>
            </div>
            {!collapsed[region] && (
              <table className="data-table">
                <thead>
                  <tr>
                    <th onClick={() => toggleSort('company_name')} className="cursor-pointer">Company</th>
                    <th>HQ</th>
                    <th>Crops</th>
                    <th onClick={() => toggleSort('weighted_score')} className="cursor-pointer">Score</th>
                    <th>Tier</th>
                    <th>Stage</th>
                    <th className="text-right" onClick={() => toggleSort('hectares_controlled')}>Hectares</th>
                    <th className="text-right" onClick={() => toggleSort('projected_revenue')}>Revenue</th>
                  </tr>
                </thead>
                <tbody>
                  {cos.map(c => (
                    <tr key={c.company_name} onClick={() => navigate(`/analyse/${encodeURIComponent(c.company_name)}`)}>
                      <td style={{ fontWeight: 600 }}>{c.company_name}</td>
                      <td style={{ color: 'var(--text-secondary)' }}>{c.hq_country}</td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                        {c.main_crops.slice(0, 3).join(', ')}{c.main_crops.length > 3 ? ` +${c.main_crops.length - 3}` : ''}
                      </td>
                      <td>{c.weighted_score.toFixed(2)}</td>
                      <td><TierBadge tier={c.tier} /></td>
                      <td><StageBadge stage={c.pipeline_stage} /></td>
                      <td className="text-right">{c.hectares_controlled ? fmtNumber(c.hectares_controlled) : '—'}</td>
                      <td className="text-right">{c.projected_revenue ? fmtCurrency(c.projected_revenue) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        ))}
      </div>
    </>
  );
}
