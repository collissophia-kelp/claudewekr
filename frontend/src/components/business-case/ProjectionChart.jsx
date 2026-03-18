import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { fmtCurrency, fmtNumber } from '../../utils/formatters';

export default function ProjectionChart({ projections }) {
  const data = projections.map(p => ({
    year: `Y${p.year}`,
    revenue: p.revenue_eur,
    litres: p.litres_required,
    hectares: p.treated_hectares,
  }));

  return (
    <ResponsiveContainer width="100%" height={250}>
      <AreaChart data={data} margin={{ left: 10, right: 20, top: 10, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="year" tick={{ fill: '#8BA4C4', fontSize: 12 }} />
        <YAxis tick={{ fill: '#8BA4C4', fontSize: 11 }} tickFormatter={v => fmtCurrency(v)} width={70} />
        <Tooltip
          contentStyle={{ background: '#162A48', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#E8EDF3' }}
          formatter={(v, name) => [
            name === 'revenue' ? fmtCurrency(v) : fmtNumber(v),
            name === 'revenue' ? 'Revenue (EUR)' : name === 'litres' ? 'Litres' : 'Treated Ha',
          ]}
        />
        <Area type="monotone" dataKey="revenue" stroke="#4CAF50" fill="rgba(76,175,80,0.2)" strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
